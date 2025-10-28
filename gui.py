

import pygame

# --- UI Components ---

class Button:
    def __init__(self, x, y, width, height, label, color=(100, 100, 200)):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.color = color
        self.font = pygame.font.Font(None, 24)

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=5)
        label_surface = self.font.render(self.label, True, (255, 255, 255))
        text_rect = label_surface.get_rect(center=self.rect.center)
        screen.blit(label_surface, text_rect)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

class ToggleSwitch:
    def __init__(self, x, y, width, height, label, is_on=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.is_on = is_on
        self.font = pygame.font.Font(None, 24)

    def draw(self, screen):
        color = (34, 139, 34) if self.is_on else (178, 34, 34)
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        label_surface = self.font.render(self.label, True, (255, 255, 255))
        text_rect = label_surface.get_rect(center=self.rect.center)
        screen.blit(label_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_on = not self.is_on
                return True
        return False

class TextInputBox:
    def __init__(self, x, y, width, height, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = ""
        self.font = font
        self.active = False
        self.color_active = pygame.Color('dodgerblue2')
        self.color_inactive = pygame.Color('lightgray')
        self.color = self.color_inactive

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)
            self.color = self.color_active if self.active else self.color_inactive
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 255, 255), self.rect)
        pygame.draw.rect(screen, self.color, self.rect, 2)
        text_surface = self.font.render(self.text, True, (0, 0, 0))
        screen.blit(text_surface, (self.rect.x + 5, self.rect.y + 5))

# --- Main UI Views ---

class CreationForm:
    def __init__(self, screen_width, screen_height):
        self.font_title = pygame.font.Font(None, 48)
        self.font_label = pygame.font.Font(None, 32)
        self.font_input = pygame.font.Font(None, 28)
        self.width = screen_width
        self.height = screen_height

        self.questions = [
            "1. What is the name or title of your justice framework?",
            "2. In 1-2 sentences, what does justice mean in this worldview?",
            "3. What are its core values or principles? (comma-separated)",
            "4. Describe your advocate's tone and personality.",
        ]
        
        self.input_boxes = []
        self.labels = []
        
        input_w = self.width * 0.6
        input_h = 35
        start_y = 150
        y_padding = 100

        for i, q in enumerate(self.questions):
            y_pos = start_y + i * y_padding
            label_surface = self.font_label.render(q, True, (255, 255, 255))
            self.labels.append((label_surface, (self.width / 2 - input_w / 2, y_pos)))
            box = TextInputBox(self.width / 2 - input_w / 2, y_pos + 40, input_w, input_h, self.font_input)
            self.input_boxes.append(box)

        self.save_button = Button(self.width / 2 - 100, start_y + len(self.questions) * y_padding, 200, 50, "Save Advocate")

    def handle_event(self, event):
        for box in self.input_boxes:
            box.handle_event(event)
        if self.save_button.is_clicked(event):
            return { 
                "name": self.input_boxes[0].text,
                "definition": self.input_boxes[1].text,
                "values": self.input_boxes[2].text,
                "tone": self.input_boxes[3].text,
            }
        return None

    def draw(self, screen):
        screen.fill((20, 20, 40)) # Dark blue background
        title_surface = self.font_title.render("Create Your Justice Advocate", True, (255, 255, 255))
        screen.blit(title_surface, (self.width / 2 - title_surface.get_width() / 2, 50))

        for label, pos in self.labels:
            screen.blit(label, pos)
        for box in self.input_boxes:
            box.draw(screen)
        
        self.save_button.draw(screen)

class ChatGUI:
    def __init__(self, agents, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Justice Council")

        # Resources
        self.background_image = pygame.image.load("resources/background.jpg").convert()
        self.background_image = pygame.transform.scale(self.background_image, (self.screen_width, self.screen_height))
        self.dialogue_box_image = pygame.image.load("resources/dialogue_box.jpg").convert_alpha()
        self.dialogue_box_image = pygame.transform.scale(self.dialogue_box_image, (self.screen_width * 0.8, 150))
        self.dialogue_box_rect = pygame.Rect(300, 700, 1080, 125)

        # Sprites
        self.sprites = {
            "Dr. Sam Iqbal": pygame.transform.scale(pygame.image.load("resources/sprites/utilitarian.jpg").convert_alpha(), (60, 100)),
            "Amara Ndlovu": pygame.transform.scale(pygame.image.load("resources/sprites/restorative.jpg").convert_alpha(), (60, 100)),
            "Jamie Reyes": pygame.transform.scale(pygame.image.load("resources/sprites/meritocracy.jpg").convert_alpha(), (60, 100)),
            "Jordan Chex": pygame.transform.scale(pygame.image.load("resources/sprites/rawlsian.jpg").convert_alpha(), (60, 100)),
        }

        # State & UI
        self.font = pygame.font.Font(None, 24)
        self.agents = agents
        self.chat_history = ["The Council is in session. What is the matter you bring before us?"]
        self.main_input_box = TextInputBox(1560 - 40 - 500, 40, 500, int(self.screen_height * 0.2), self.font)
        self.create_advocate_button = Button(self.screen_width - 220, self.screen_height - 60, 200, 40, "Create Advocate")
        self.toggle_switches = self._create_toggle_switches()

    def _create_toggle_switches(self):
        toggles = []
        x, y = 40, 40
        for agent in self.agents.values():
            toggles.append(ToggleSwitch(x, y, 150, 30, agent.profile.name))
            x += 160
        return toggles

    def handle_event(self, event):
        self.main_input_box.handle_event(event)
        for toggle in self.toggle_switches:
            toggle.handle_event(event)

    def draw(self, screen):
        screen.blit(self.background_image, (0, 0))
        screen.blit(self.dialogue_box_image, (self.screen_width * 0.1, 675))
        
        if self.chat_history:
            render_wrapped_text(self.chat_history[-1], self.font, (0, 0, 0), self.dialogue_box_rect, screen)

        self.main_input_box.draw(screen)
        self.create_advocate_button.draw(screen)
        for toggle in self.toggle_switches:
            toggle.draw(screen)
        
        self._draw_sprites(screen)

    def _draw_sprites(self, screen):
        sprite_positions = {
            "Dr. Sam Iqbal": (760, 530),
            "Amara Ndlovu": (860, 415),
            "Jamie Reyes": (650, 415),
            "Jordan Chex": (760, 305),
        }
        for toggle in self.toggle_switches:
            if toggle.is_on and toggle.label in self.sprites:
                screen.blit(self.sprites[toggle.label], sprite_positions[toggle.label])

# --- Utility Functions ---

def render_wrapped_text(text, font, color, rect, surface):
    padding = 10
    x, y = rect.x + padding, rect.y + padding
    max_width = rect.width - 2 * padding
    line_height = font.get_linesize()
    paragraphs = text.split("\n")

    for para in paragraphs:
        words = para.split(" ")
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if font.size(candidate)[0] <= max_width:
                line = candidate
            else:
                if y + line_height > rect.bottom - padding: return
                surface.blit(font.render(line, True, color), (x, y))
                y += line_height
                line = word
        if line:
            if y + line_height > rect.bottom - padding: return
            surface.blit(font.render(line, True, color), (x, y))
            y += line_height

