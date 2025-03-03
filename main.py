import random
import math
from math import cos, sin, radians, atan2, degrees
import json
from kivy.config import Config
from kivy.core.audio import SoundLoader
from kivy.properties import NumericProperty, ListProperty
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.graphics import Color, Ellipse, Rectangle, Line, RoundedRectangle
from kivy.animation import Animation
from kivy.uix.label import Label
from kivy.uix.widget import Widget

# Game Constants
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 700  # Adjusted height for better UI placement
INITIAL_LIVES = 3
BULLET_SPEED = 60  # Increased bullet speed
MISSILE_SPEED = 30
GRAVITY = 1
POWER_UP_CHANCE = 0.005  # Reduced from 0.01 for better balance

Config.set('graphics', 'width', str(WINDOW_WIDTH))
Config.set('graphics', 'height', str(WINDOW_HEIGHT))

# Modern Color Scheme with Neon Dark Theme
COLORS = {
    'primary': [0, 1, 0.8, 1],        # Neon Cyan
    'secondary': [0.2, 0.8, 1, 1],    # Bright Blue
    'accent': [1, 0.2, 0.4, 0.9],     # Neon Pink
    'success': [0.4, 1, 0.4, 1],      # Neon Green
    'warning': [1, 0.8, 0, 1],        # Neon Yellow
    'background': [0.06, 0.06, 0.08, 1], # Dark Background
    'text': [0.9, 0.9, 1, 1],         # Light Text
    'block_glow': [1, 0.2, 0.4, 0.3]  # Pink glow for blocks
}

class GameObject:
    def __init__(self, pos, size, color):
        self.pos = list(pos)
        self.size = size
        self.color = color
        self.shape = None

class Ball(GameObject):
    def __init__(self, pos):
        super().__init__(pos, (40, 40), [random.uniform(0.5, 1), random.uniform(0.5, 1), random.uniform(0.5, 1), 1])
        self.speed = random.uniform(0.2, 0.4)
        self.direction = random.choice([-1, 1])

class PowerUp(GameObject):


    def __init__(self, pos, type):
        color = {
            'speed': COLORS['success'],
            'shield': [0, 1, 1, 1],
            'double_score': COLORS['warning']
        }.get(type, COLORS['primary'])
        super().__init__(pos, (30, 30), color)
        self.type = type
        self.active = True

class Particle(GameObject):
    def __init__(self, pos, color):
        super().__init__(pos, (5, 5), color)
        self.life = 1.0
        self.velocity = [random.uniform(-2, 2), random.uniform(-2, 2)]


class CanonGame(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup_game_state()
        self.setup_ui()
        self.setup_game_objects()
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self.bind_events()  # Keep only one instance
        Clock.schedule_interval(self.update, 1/60)

        with self.canvas.after:
            self.trajectory_line = Line(points=[], width=2, color=COLORS['accent'])



    def setup_ui(self):
        self.setup_labels()
        self.setup_buttons()
        self.setup_game_elements()
        self.help_clicked = False  # Initialize help state

    def setup_labels(self):
        # Modern label style with shadow effect
        label_style = {
            'font_size': 24,
            'color': COLORS['text'],
            'bold': True,
            'outline_width': 1,
            'outline_color': [0, 0, 0, 0.5]
        }
        
        # Game Title
        self.title_label = Label(
            text="CANON SHOOTER",
            pos=(Window.width / 2 - 150, Window.height - 100),
            font_size=48,
            color=COLORS['primary'],
            bold=True,
            outline_width=2,
            outline_color=[0, 0, 0, 0.5]
        )
        self.add_widget(self.title_label)
        
        # Score Panel (Top Left)
        score_panel_y = Window.height - 120
        self.score_label = Label(
            text="Score: 0",
            pos=(30, score_panel_y),
            **label_style
        )
        self.add_widget(self.score_label)
        
        self.level_label = Label(
            text="Level: 1",
            pos=(30, score_panel_y - 40),
            **label_style
        )
        self.add_widget(self.level_label)
        
        self.missile_label = Label(
            text=f"Missiles: {self.missile_number}",
            pos=(30, score_panel_y - 80),
            **label_style
        )
        self.add_widget(self.missile_label)

        # Status Panel (Top Right)
        status_panel_y = Window.height - 120
        self.high_score_label = Label(
            text=f"High Score: {self.high_score}",
            pos=(Window.width - 200, status_panel_y),
            **label_style
        )
        self.add_widget(self.high_score_label)

        # Power-up Status with modern styling
        self.power_up_status = Label(
            text="",
            pos=(Window.width - 200, status_panel_y - 60),
            font_size=20,
            color=COLORS['warning'],
            bold=True,
            outline_width=1,
            outline_color=[0, 0, 0, 0.3]
        )
        self.add_widget(self.power_up_status)
        
        # Help text (left side, initially hidden)
        self.help_label = Label(
            text="",
            pos=(200, Window.height / 2 - 300),  # Moved right by adjusting x coordinate
            size_hint=(None, None),
            color=COLORS['text'],
            font_size=16,  # Slightly smaller font for better fit
            halign='left',
            valign='middle',
            width=300  # Fixed width for better text wrapping
        )
        self.help_label.bind(texture_size=self.help_label.setter('size'))
        self.add_widget(self.help_label)

    def setup_buttons(self):
        # Modern button style with gradient effect
        button_style = {
            'size_hint': (None, None),
            'size': (140, 45),
            'background_color': [*COLORS['primary'][:3], 0.9],
            'color': COLORS['background'],
            'bold': True,
            'font_size': 18,
            'border': (0, 0, 0, 0),
            'background_normal': ''
        }
        
        # Button panel on the left side
        button_x = 30
        button_start_y = Window.height - 250
        button_spacing = 60
        
        buttons = [
            ('Pause', self.toggle_pause),  # Add pause button
            ('Help', self.show_help),
            ('Restart', self.reset_game),
            ('Save Game', self.save_game),
            ('Load Game', self.load_game)
        ]
        
        for idx, (text, callback) in enumerate(buttons):
            btn = Button(
                text=text,
                pos=(button_x, button_start_y - (idx * button_spacing)),
                **button_style
            )
            # Add hover effect
            btn.bind(
                on_press=lambda btn: setattr(btn, 'background_color', [*COLORS['secondary'][:3], 0.9]),
                on_release=lambda btn, cb=callback: (cb(btn), setattr(btn, 'background_color', [*COLORS['primary'][:3], 0.9]))
            )
            self.add_widget(btn)

    def setup_game_elements(self):
        # Draw background first
        with self.canvas.before:
            Color(*COLORS['background'])
            self.background = Rectangle(pos=self.pos, size=Window.size)
            
        with self.canvas:
            Color(*COLORS['primary'])
            self.cannon_base = RoundedRectangle(
                pos=(Window.width / 2 + self.x, 30),
                size=(50, 20),
                radius=[5,]
            )
            
            Color(*COLORS['secondary'])
            self.cannon = RoundedRectangle(
                pos=(Window.width / 2 + self.x + 15, 40),
                size=(20, 40),
                radius=[5,]
            )
            
            Color(*COLORS['accent'])
            self.bullet = RoundedRectangle(
                pos=(self.cannon.pos[0] + 5, 70),
                size=(15, 35),  # Increased bullet size
                radius=[7,]  # Slightly larger radius for better appearance
            )
            
            Color(*COLORS['success'])
            self.missile = RoundedRectangle(
                pos=(self.cannon.pos[0] + 5, 70),
                size=(10, 35),
                radius=[5,]
            )

    def setup_game_state(self):
        # Add pause state
        self.paused = False
        
        # Grace period
        self.grace_period = True
        Clock.schedule_once(self.end_grace_period, 2.0)  # 2 seconds grace period
        
        # Initialize destroyed balls counter
        self.destroyed_balls = 0
        
        # Game state
        self.score = 0
        self.level = 1
        self.lives = INITIAL_LIVES
        self.game_over = False
        self.combo = 0
        self.combo_timer = None
        
        # Weapon state
        self.bullet_state = 'ready'
        self.missile_state = 'not ready'
        self.missile_number = 3
        self.bullet_speed = BULLET_SPEED
        self.missile_speed = MISSILE_SPEED
        self.bullet_heading = 90
        self.missile_heading = 90
        
        # Movement and position
        self.x = 0
        self.mouse_pos = (0, 0)
        self.bullet_dx = self.bullet_speed * cos(radians(self.bullet_heading))
        self.bullet_dy = self.bullet_speed * sin(radians(self.bullet_heading))
        self.missile_dx = self.missile_speed * cos(radians(self.missile_heading))
        self.missile_dy = self.missile_speed * sin(radians(self.missile_heading))
        
        # Power-ups and special features
        self.power_ups = []
        self.power_up_types = ['speed', 'shield', 'double_score', 'auto_aim', 'rapid_fire']
        self.particles = []
        self.has_shield = False
        self.score_multiplier = 1
        self.bullet_speed_boost = 1
        self.auto_aim = False
        self.has_rapid_fire = False
        self.rapid_fire_timer = None
        
        # Game objects
        self.Balls_list = []
        self.Blocks_list = []  # Restore blocks list
        
        try:

            with open('high_score.json', 'r') as f:
                self.high_score = json.load(f)['high_score']
        except:
            self.high_score = 0

    def end_grace_period(self, dt):
        self.grace_period = False

    def setup_game_objects(self):
        # Load audio files with error handling
        self.sounds = {}
        sound_files = {
            'background': 'background.wav',
            'bullet': 'bullet.wav',
            'missile': 'missile.wav',
            'pop': 'pop.wav',
            'game_over': 'gameOver.wav'
        }
        
        for sound_name, file_name in sound_files.items():
            try:
                sound = SoundLoader.load(file_name)
                if sound:
                    if sound_name == 'background':
                        sound.volume = 0.5
                        sound.loop = True
                    self.sounds[sound_name] = sound
            except:
                print(f"Could not load {file_name}")
        
        # Start background music if available
        if 'background' in self.sounds:
            self.sounds['background'].play()

    def play_sound(self, sound_name):
        if sound_name in self.sounds:
            self.sounds[sound_name].play()

    def bind_events(self):
        Window.bind(mouse_pos=self.on_mouse_pos)
        Window.bind(on_mouse_down=self.on_mouse_down)
        Window.bind(on_mouse_up=self.on_mouse_up)


    def save_game(self, instance):
        save_data = {
            'score': self.score,
            'level': self.level,
            'Missiles': self.missile_number
        }
        with open('save_game.json', 'w') as f:
            json.dump(save_data, f)

    def load_game(self, instance):
        try:
            with open('save_game.json', 'r') as f:
                save_data = json.load(f)
                self.score = save_data['score']
                self.level = save_data['level']
                self.missile_number = save_data['Missiles']
                self.update_ui()
                
                # Clear existing game objects
                self.clear_game_objects()
        except FileNotFoundError:
            print("Save file not found")


    def show_help(self, instance):
        if self.help_clicked:
            self.help_label.text = ""
            self.help_clicked = False
        else:
            # Update help text position
            self.help_label.pos = (200, Window.height / 2 - 300)  # Moved right and centered vertically
            
            self.help_label.text = """🎮 CANON SHOOTER - GAME GUIDE 🎮

[[ GAME CONTROLS ]]
• Mouse Controls:
  - Left Click: Fire weapon
  - Right Click: Switch between bullet/missile
  - Mouse Movement: Aim cannon
• Keyboard Controls:
  - A/D keys: Move cannon left/right
  - Left/Right arrows: Fine-tune aim
  - Spacebar: Fire weapon
• Game Controls:
  - Help Button: Show/hide this guide
  - Pause Button: Pause/resume game
  - Restart Button: Start new game
  - Save/Load: Save or load game progress

[[ OBJECTIVE ]] 
Defend your position by shooting incoming balls before they reach the bottom. Each successful hit increases your score and helps you level up!

[[ WEAPONS SYSTEM ]] 
Primary Weapon - Bullets 🔫: Unlimited ammunition, Single target damage, Quick reload time, Affected by gravity
Special Weapon - Missiles 🚀: Limited supply, Area damage effect, Destroys multiple targets, Earn 1 missile per 10 destroyed balls

[[ POWER-UPS ]] 
Speed Boost 🟢: Doubles bullet speed (10s) | Shield 🔵: Blocks one missed ball (15s) | Double Score 🟡: Doubles all points (20s)

[[ SCORING SYSTEM ]] 
Regular Hit: 1 point × combo multiplier | Missile Hit: 3 points (shared among targets) | Combo System: Consecutive hits increase points
Max Combo: 10x multiplier | Combo Timer: 2 seconds between hits

[[ PROGRESSION ]] 
Level Advancement: Every 15 points = New level | Higher levels increase: Ball spawn rate, Ball speed, Maximum balls on screen

[[ PRO TIPS ]] 
Save missiles for emergency situations | Build and maintain combos for high scores | Collect power-ups strategically | Watch for ball patterns
Practice aim prediction | Keep track of your shield timer

🏆 Good luck, Commander! Beat that high score! 🏆"""
        self.help_clicked = True


    def shoot(self):
        if self.bullet_state == 'ready':
            self.play_sound('bullet')
            self.bullet_state = 'fire'
        elif self.missile_state == 'ready' and self.missile_number > 0:
            self.play_sound('missile')
            self.missile_state = 'fire'
            self.missile_number -= 1
            self.missile_label.text = f'Missiles: {self.missile_number}'


    def move_right(self):
        target_x = self.x + 10
        if Window.width / 2 + target_x < Window.width - 50:  # Boundary check
            self.x = target_x
            # Direct position updates without animation
            self.cannon_base.pos = (Window.width / 2 + self.x, 30)
            self.cannon.pos = (Window.width / 2 + self.x + 15, 40)
            if self.bullet_state == 'ready':
                self.bullet.pos = (self.cannon.pos[0] + 5, 70)
            if self.missile_state == 'ready':
                self.missile.pos = (self.cannon.pos[0] + 5, 70)

    def move_left(self):
        target_x = self.x - 10
        if Window.width / 2 + target_x > 0:  # Boundary check
            self.x = target_x
            # Direct position updates without animation
            self.cannon_base.pos = (Window.width / 2 + self.x, 30)
            self.cannon.pos = (Window.width / 2 + self.x + 15, 40)
            if self.bullet_state == 'ready':
                self.bullet.pos = (self.cannon.pos[0] + 5, 70)
            if self.missile_state == 'ready':
                self.missile.pos = (self.cannon.pos[0] + 5, 70)

    def turn_left(self):
        if self.bullet_state == 'ready':
            self.bullet_heading += 10
            self.update_bullet_velocity()
            self.update_trajectory_line()
        elif self.missile_state == 'ready':
            self.missile_heading += 10
            self.update_missile_velocity()
            self.update_trajectory_line()

    def turn_right(self):
        if self.bullet_state == 'ready':
            self.bullet_heading -= 10
            self.update_bullet_velocity()
            self.update_trajectory_line()
        elif self.missile_state == 'ready':
            self.missile_heading -= 10
            self.update_missile_velocity()
            self.update_trajectory_line()

    def switch_bullet_missile(self):
        if self.bullet_state == 'ready':
            self.bullet_state = 'not ready'
            self.missile_state = 'ready'
        elif self.missile_state == 'ready':
            self.bullet_state = 'ready'
            self.missile_state = 'not ready'

    def update_bullet_velocity(self):
        self.bullet_dx = self.bullet_speed * cos(radians(self.bullet_heading))
        self.bullet_dy = self.bullet_speed * sin(radians(self.bullet_heading))

    def update_missile_velocity(self):
        self.missile_dx = self.missile_speed * cos(radians(self.missile_heading))
        self.missile_dy = self.missile_speed * sin(radians(self.missile_heading))

    def update_trajectory_line(self):
        if self.game_over:
            self.trajectory_line.points = (0,0,0,0)
        elif self.bullet_state == 'ready':
            start_x = self.bullet.pos[0] + self.bullet.size[0] / 2
            start_y = self.bullet.pos[1] + self.bullet.size[1]
            end_x = start_x + 100 * cos(radians(self.bullet_heading))
            end_y = start_y + 100 * sin(radians(self.bullet_heading))
            self.trajectory_line.points = (start_x, start_y, end_x, end_y)
        elif self.missile_state == 'ready':
            start_x = self.missile.pos[0] + self.missile.size[0] / 2
            start_y = self.missile.pos[1] + self.missile.size[1]
            end_x = start_x + 100 * cos(radians(self.missile_heading))
            end_y = start_y + 100 * sin(radians(self.missile_heading))
            self.trajectory_line.points = (start_x, start_y, end_x, end_y)


    def update_power_up_status(self):
        status = []
        if self.bullet_speed_boost > 1:
            status.append("Speed Boost Active!")
        if self.has_shield:
            status.append("Shield Active!")
        if self.score_multiplier > 1:
            status.append("Double Score Active!")
        
        self.power_up_status.text = "\n".join(status)
        # Update color based on active power-ups
        self.power_up_status.color = (1, 1, 0, 1) if status else (0.9, 0.9, 1, 1)

    def apply_power_up(self, power_up):
        if power_up.type == 'speed':
            self.bullet_speed_boost = 2
            self.bullet_speed = BULLET_SPEED * 2  # Directly multiply base speed
            Clock.schedule_once(lambda dt: self.reset_power_up('speed'), 10)
        elif power_up.type == 'shield':
            self.has_shield = True
            # Add visual feedback for shield
            with self.canvas:
                Color(0, 1, 1, 0.3)  # Cyan color with transparency
                self.shield_visual = Ellipse(
                    pos=(self.cannon.pos[0] - 15, self.cannon.pos[1] - 15),
                    size=(80, 80)  # Larger shield size for better visibility
                )
            Clock.schedule_once(lambda dt: self.reset_power_up('shield'), 15)
        elif power_up.type == 'double_score':
            self.score_multiplier = 2
            Clock.schedule_once(lambda dt: self.reset_power_up('double_score'), 20)
        
        self.create_explosion(power_up.pos, power_up.color)
        self.update_power_up_status()


    def reset_power_up(self, power_type):
        if power_type == 'speed':
            self.bullet_speed_boost = 1
            self.bullet_speed = BULLET_SPEED
        elif power_type == 'shield':
            self.has_shield = False
            # Remove shield visual
            if hasattr(self, 'shield_visual'):
                self.canvas.remove(self.shield_visual)
                delattr(self, 'shield_visual')
        elif power_type == 'double_score':
            self.score_multiplier = 1
        self.update_power_up_status()  # Update status after reset

    def on_mouse_pos(self, window, pos):
        self.mouse_pos = pos
        # Update cannon rotation based on mouse position
        if not self.game_over:
            dx = pos[0] - (self.cannon.pos[0] + self.cannon.size[0]/2)
            dy = pos[1] - (self.cannon.pos[1] + self.cannon.size[1]/2)
            angle = degrees(atan2(dy, dx))
            
            if self.bullet_state == 'ready':
                self.bullet_heading = angle
                self.update_bullet_velocity()
                self.update_trajectory_line()
            elif self.missile_state == 'ready':
                self.missile_heading = angle
                self.update_missile_velocity()
                self.update_trajectory_line()

    def on_mouse_down(self, window, x, y, button, modifiers):
        if button == 'left':
            self.shoot()
        elif button == 'right':
            self.switch_bullet_missile()

    def on_mouse_up(self, window, x, y, button, modifiers):
        pass

    def reset_auto_aim(self, dt):
        self.auto_aim = False

    def reset_rapid_fire(self, dt):
        self.has_rapid_fire = False
        if self.rapid_fire_timer:
            self.rapid_fire_timer.cancel()

    def auto_shoot(self, dt):
        if self.has_rapid_fire:
            self.shoot()

    def spawn_power_up(self):
        if random.random() < 0.01:  # 1% chance each frame
            power_type = random.choice(['speed', 'shield', 'double_score'])
            power_up = PowerUp(
                (random.randint(0, Window.width-30), Window.height),
                power_type
            )
            self.power_ups.append(power_up)
            with self.canvas:
                # Different colors for different power-ups
                if power_type == 'speed':
                    Color(0, 1, 0, 1)  # Green for speed
                elif power_type == 'shield':
                    Color(0, 1, 1, 1)  # Cyan for shield
                else:
                    Color(1, 1, 0, 1)  # Yellow for double score
                power_up.shape = Rectangle(pos=power_up.pos, size=power_up.size)

    def update_particles(self, dt):
        for particle in self.particles[:]:
            particle.life -= 0.02
            if particle.life <= 0:
                if particle.shape:
                    self.canvas.remove(particle.shape)
                self.particles.remove(particle)
                continue
            
            particle.pos[0] += particle.velocity[0]
            particle.pos[1] += particle.velocity[1]
            if particle.shape:
                particle.shape.pos = particle.pos


    def create_explosion(self, pos, color):
        # Determine number of particles based on explosion size
        num_particles = 40 if self.missile_state == 'fire' else 20
        for _ in range(num_particles):
            particle = Particle(pos, color)
            # Bigger explosion radius for missile
            if self.missile_state == 'fire':
                particle.velocity = [random.uniform(-4, 4), random.uniform(-4, 4)]
            self.particles.append(particle)
            with self.canvas:
                Color(*particle.color, particle.life)
                particle.shape = Ellipse(pos=particle.pos, size=(5, 5))

    def update_projectiles(self, dt):
        if self.bullet_state == 'fire':
            self.bullet.pos = (
                self.bullet.pos[0] + self.bullet_dx,
                self.bullet.pos[1] + self.bullet_dy
            )
            self.bullet_dy -= GRAVITY

            # Reset bullet if it goes out of bounds
            if (self.bullet.pos[1] < 0 or self.bullet.pos[1] > Window.height or 
                self.bullet.pos[0] < 0 or self.bullet.pos[0] > Window.width):
                self.reset_bullet()

        if self.missile_state == 'fire':
            self.missile.pos = (
                self.missile.pos[0] + self.missile_dx,
                self.missile.pos[1] + self.missile_dy
            )
            self.missile_dy -= 0.1

            # Keep missile in bounds and bounce off walls
            if self.missile.pos[0] < 0:
                self.missile.pos = (0, self.missile.pos[1])
                self.missile_dx = abs(self.missile_dx)  # Bounce right
            elif self.missile.pos[0] > Window.width - self.missile.size[0]:
                self.missile.pos = (Window.width - self.missile.size[0], self.missile.pos[1])
                self.missile_dx = -abs(self.missile_dx)  # Bounce left
                
            if self.missile.pos[1] > Window.height - self.missile.size[1]:
                self.missile.pos = (self.missile.pos[0], Window.height - self.missile.size[1])
                self.missile_dy = -abs(self.missile_dy)  # Bounce down
            elif self.missile.pos[1] < 0:
                self.reset_missile()  # Only reset when hitting bottom



    def spawn_enemies(self):
        # Spawn balls with more gradual difficulty increase
        max_balls = 3 + (self.level // 2)  # Slower increase in max balls (every 2 levels)
        spawn_chance = 0.01 + (self.level * 0.002)  # Reduced spawn rate increase per level
        
        if len(self.Balls_list) < max_balls and random.random() < spawn_chance:
            pos = (random.randint(100, Window.width - 100), Window.height)
            with self.canvas:
                # Balls get more vibrant colors at higher levels
                color_intensity = min(0.5 + (self.level * 0.03), 1.0)  # Reduced color intensity change
                Color(
                    random.uniform(color_intensity, 1),
                    random.uniform(color_intensity, 1),
                    random.uniform(color_intensity, 1),
                    1
                )
                ball = RoundedRectangle(
                    pos=pos,
                    size=(40, 40),
                    radius=[20,]
                )
            self.Balls_list.append(ball)





    def toggle_pause(self, instance=None):
        self.paused = not self.paused
        
        # Remove existing pause elements
        if hasattr(self, 'pause_overlay'):
            self.canvas.before.remove(self.pause_overlay)
            delattr(self, 'pause_overlay')
        if hasattr(self, 'pause_label'):
            self.remove_widget(self.pause_label)
            delattr(self, 'pause_label')
        
        if self.paused:
            # Create semi-transparent overlay in canvas.before to avoid accumulation
            with self.canvas.before:
                Color(0, 0, 0, 0.5)
                self.pause_overlay = Rectangle(pos=(0, 0), size=Window.size)
            
            # Create pause label
            self.pause_label = Label(
                text="PAUSED\nClick Pause to Continue",
                pos=(Window.width / 2 - 150, Window.height / 2),
                font_size=36,
                color=[1, 1, 1, 1],
                bold=True,
                halign='center'
            )
            self.add_widget(self.pause_label)
            
            # Pause background music if it exists
            if 'background' in self.sounds and self.sounds['background'].state == 'play':
                self.sounds['background'].stop()
        else:
            # Resume background music if it exists
            if 'background' in self.sounds and not self.game_over:
                self.sounds['background'].play()


    def update(self, dt):
        if self.game_over or self.paused:
            return
            
        try:
            self.update_trajectory_line()
            self.update_power_ups(dt)
            self.update_particles(dt)
            self.update_projectiles(dt)
            # Update shield visual position if it exists
            if hasattr(self, 'shield_visual'):
                self.shield_visual.pos = (self.cannon.pos[0] - 15, self.cannon.pos[1] - 15)
            if not self.grace_period:
                self.spawn_enemies()
            self.update_enemies(dt)
            if not self.game_over:
                self.check_collisions()
                self.update_ui()
        except Exception as e:
            print(f"Error in update: {e}")
            self.play_sound('game_over')
            self.end_game()

    def update_ui(self):
        # Update score and level display
        self.score_label.text = f"Score: {self.score}"
        self.level_label.text = f"Level: {self.level}"
        self.missile_label.text = f"Missiles: {self.missile_number}"
        
        # Update power-up status
        status = []
        if self.bullet_speed_boost > 1:
            status.append("Speed Boost")
        if self.has_shield:
            status.append("Shield Active")
        if self.score_multiplier > 1:
            status.append("Double Score")
        self.power_up_status.text = "\n".join(status)

    def update_power_ups(self, dt):
        # Spawn power-ups with controlled randomness
        if random.random() < POWER_UP_CHANCE:
            power_type = random.choice(['speed', 'shield', 'double_score'])
            pos = (random.randint(50, Window.width-50), Window.height)
            power_up = PowerUp(pos, power_type)
            self.power_ups.append(power_up)
            with self.canvas:
                Color(*power_up.color)
                power_up.shape = Rectangle(pos=power_up.pos, size=power_up.size)

        # Update existing power-ups
        for power_up in self.power_ups[:]:
            power_up.pos[1] -= 3  # Slightly faster fall speed
            if power_up.shape:
                power_up.shape.pos = power_up.pos
            
            if power_up.pos[1] < 0:
                self.remove_power_up(power_up)
            elif self.check_collision(self.cannon, power_up):
                self.apply_power_up(power_up)
                self.remove_power_up(power_up)


    def update_missile_number(self):
        # Only update missile number for regular bullet hits, not missile explosions
        if self.score > 0 and self.score % 5 == 0 and self.bullet_state == 'ready':
            self.missile_number += 1
            self.missile_label.text = f'Missiles: {self.missile_number}'

    def update_level(self):
        old_level = self.level
        new_level = self.score // 15 + 1  # Changed from 10 to 15 points per level for slower progression
        
        if new_level > old_level:
            self.level = new_level
            self.level_label.text = f"Level: {self.level}"
            self.play_sound('level_up')






    def reset_bullet(self):
        self.bullet.pos = (self.cannon.pos[0] + 15, 60)
        self.bullet_state = 'ready'
        self.update_bullet_velocity()
        self.trajectory_line.points = []

    def reset_missile(self):
        self.missile.pos = (self.cannon.pos[0] + 15, 60)
        self.missile_state = 'ready'
        self.update_missile_velocity()
        self.trajectory_line.points = []

    def update_score(self, points=1):
        self.score += points * self.score_multiplier
        self.score_label.text = f"Score: {self.score}"
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()
        self.update_level()

    def save_high_score(self):
        with open('high_score.json', 'w') as f:
            json.dump({'high_score': self.high_score}, f)

    def end_game(self):
        self.game_over = True
        if 'background' in self.sounds:
            self.sounds['background'].stop()
        self.play_sound('game_over')
            
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()
            
        # Clear only game elements, not UI
        self.clear_game_objects()
        
        # Create semi-transparent overlay
        with self.canvas:
            Color(0, 0, 0, 0.7)
            Rectangle(pos=(0, 0), size=Window.size)
        
        game_over_text = f'''GAME OVER

Final Score: {self.score}
High Score: {self.high_score}
Level Reached: {self.level}

Press Restart to Play Again'''

        self.game_over_label = Label(
            text=game_over_text,
            pos=(Window.width / 2 - 150, Window.height / 2),
            font_size=36,
            color=[1, 1, 1, 1],
            bold=True,
            outline_width=2,
            outline_color=[0, 0, 0, 0.5],
            halign='center'
        )
        self.add_widget(self.game_over_label)

    def is_out_of_bounds(self, pos):
        return (pos[0] < 0 or pos[0] > Window.width or
                pos[1] < 0 or pos[1] > Window.height)

    def remove_power_up(self, power_up):
        if power_up.shape:
            self.canvas.remove(power_up.shape)
        self.power_ups.remove(power_up)

    def check_collision(self, obj1, obj2):
        # Improved collision detection with proper hitbox
        x1, y1 = obj1.pos if isinstance(obj1.pos, tuple) else tuple(obj1.pos)
        x2, y2 = obj2.pos if isinstance(obj2.pos, tuple) else tuple(obj2.pos)
        
        return (x1 < x2 + obj2.size[0] and
                x1 + obj1.size[0] > x2 and
                y1 < y2 + obj2.size[1] and
                y1 + obj1.size[1] > y2)

    def update_enemies(self, dt):
        if self.grace_period:
            return
            
        for ball in self.Balls_list[:]:
            try:
                # Base speed increases with level
                base_speed = 0.2 + (0.01 * self.level)
                # More complex movement patterns at higher levels
                movement_intensity = 1 + (self.level * 0.1)
                
                ball.pos = (
                    ball.pos[0] + math.sin(ball.pos[1] / 50) * 2 * movement_intensity,
                    ball.pos[1] - base_speed
                )
                
                if ball.pos[1] < -40:
                    if not self.has_shield:
                        self.play_sound('game_over')
                        self.end_game()
                        return
                    else:
                        self.remove_ball(ball)
                        self.has_shield = False
                        self.create_explosion(ball.pos, [0, 1, 1, 1])
                        if hasattr(self, 'shield_visual'):
                            self.canvas.remove(self.shield_visual)
                            delattr(self, 'shield_visual')
                        self.update_power_up_status()
            except Exception as e:
                print(f"Error updating ball: {e}")
                self.remove_ball(ball)
                    
        # Update blocks with improved movement
        for block in self.Blocks_list[:]:  # Use slice copy for safe iteration
            try:
                # Update the block's position
                current_x, current_y = block.pos
                new_x = current_x + math.sin(current_y / 100)
                new_y = current_y - (0.5 + self.level * 0.05)
                
                # Update the block's position directly
                block.pos = (new_x, new_y)
                
                # Remove block if it's below the screen
                if new_y < -15:
                    self.remove_block(block)
            except Exception as e:
                print(f"Error updating block: {e}")
                self.remove_block(block)


    def check_collisions(self):
        # Check power-up collisions first
        for power_up in self.power_ups[:]:
            if power_up.active and self.check_collision(self.cannon, power_up):
                self.apply_power_up(power_up)
                self.remove_power_up(power_up)
                return  # Prevent multiple power-up collections in same frame

        # Check bullet collisions
        if self.bullet_state == 'fire':
            for ball in self.Balls_list[:]:
                if self.check_collision(self.bullet, ball):
                    self.handle_ball_hit(ball)
                    self.reset_bullet()
                    break

        # Check missile collisions
        if self.missile_state == 'fire':
            targets_hit = len(self.Balls_list)
            if targets_hit > 0:
                base_points = 3 // targets_hit
                extra_points = 3 % targets_hit
                explosion_pos = self.missile.pos
                self.create_explosion(explosion_pos, COLORS['warning'])
                remaining_extra = extra_points
                for ball in self.Balls_list[:]:
                    points = base_points + (1 if remaining_extra > 0 else 0)
                    remaining_extra -= 1
                    self.handle_ball_hit(ball, is_missile=True, points=points)
                    self.create_explosion(ball.pos, [0.5, 0.5, 1, 1])
                self.reset_missile()







    def handle_ball_hit(self, ball, is_missile=False, points=None):
        self.remove_ball(ball)
        
        if is_missile:
            self.score += int(points)  # Ensure integer points
        else:
            self.combo += 1
            combo_bonus = self.combo if self.combo < 10 else 10  # Cap combo at 10x
            self.score += int(self.score_multiplier * combo_bonus)  # Ensure integer multiplication
            
            # Track destroyed balls and award missile every 10 balls
            if not hasattr(self, 'destroyed_balls'):
                self.destroyed_balls = 0
            self.destroyed_balls += 1
            
            if self.destroyed_balls >= 10:
                self.missile_number += 1
                self.missile_label.text = f'Missiles: {self.missile_number}'
                self.destroyed_balls = 0  # Reset counter
            
        self.score_label.text = f"Score: {self.score}" + ("" if is_missile else f" (Combo: x{self.combo})")
        self.update_level()
        self.play_sound('pop')
        self.create_explosion(ball.pos, [0.5, 0.5, 1, 1])
        
        # Reset combo timer only for regular hits
        if not is_missile and self.combo_timer:
            self.combo_timer.cancel()
        if not is_missile:
            self.combo_timer = Clock.schedule_once(self.reset_combo, 2.0)







    def remove_ball(self, ball):
        if ball in self.Balls_list:
            self.canvas.remove(ball)
            self.Balls_list.remove(ball)

    def reset_combo(self, dt):


        self.combo = 0
        self.score_label.text = f"Score: {self.score}"
        
    def reset_game(self, instance=None):
        # Clear pause state and elements first
        self.paused = False
        self.grace_period = True
        Clock.schedule_once(self.end_grace_period, 2.0)
        if hasattr(self, 'pause_elements'):
            for element in self.pause_elements[:]:
                try:
                    if isinstance(element, Widget):
                        self.remove_widget(element)
                    elif hasattr(element, 'canvas'):
                        self.canvas.remove(element)
                except:
                    pass
            self.pause_elements.clear()
        
        # Remove game over label if it exists
        if hasattr(self, 'game_over_label'):
            self.remove_widget(self.game_over_label)
            
        # Reset help state and remove help label
        self.help_clicked = False
        self.help_label.text = ""
            
        self.game_over = False
        self.score = 0
        self.level = 1
        self.missile_number = 3
        self.bullet_state = 'ready'
        self.missile_state = 'not ready'
        self.bullet_speed = BULLET_SPEED
        self.missile_speed = MISSILE_SPEED
        self.destroyed_balls = 0
        
        # Reset power-ups
        self.has_shield = False
        self.score_multiplier = 1
        self.bullet_speed_boost = 1
        
        # Clear all game objects
        self.clear_game_objects()
        
        # Clear and recreate canvas elements
        self.canvas.clear()
        self.setup_game_elements()
        
        # Recreate trajectory line
        with self.canvas.after:
            self.trajectory_line = Line(points=[], width=2, color=COLORS['accent'])
        
        # Reset UI
        self.setup_labels()
        self.setup_buttons()
        self.update_ui()
        
        # Restart music
        if 'background' in self.sounds:
            self.sounds['background'].play()

    def update_labels(self):
        self.score_label.text = f"Score: {self.score}"
        self.level_label.text = f"Level: {self.level}"
        self.missile_label.text = f"Missiles: {self.missile_number}"

    def clear_game_objects(self):
        # Clear shield visual if it exists
        if hasattr(self, 'shield_visual'):
            self.canvas.remove(self.shield_visual)
            delattr(self, 'shield_visual')
    
        # Clear particles
        for particle in self.particles[:]:
            if particle.shape:
                self.canvas.remove(particle.shape)
        self.particles.clear()
        
        # Clear other game objects
        for ball in self.Balls_list[:]:
            self.remove_ball(ball)
        for power_up in self.power_ups[:]:
            self.remove_power_up(power_up)
            
        self.Balls_list.clear()
        self.power_ups.clear()
        
    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'd':
            self.move_right()
        elif keycode[1] == 'a':
            self.move_left()
        elif keycode[1] == 'left':
            self.turn_left()
        elif keycode[1] == 'right':
            self.turn_right()
        elif keycode[1] == 'spacebar':
            self.shoot()



class CanonApp(App):
    def build(self):
        return CanonGame()


if __name__ == '__main__':
    CanonApp().run()