
import pygame

class ToggleSwitch:
    def __init__(self, x, y, width, height, label, is_on=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.is_on = is_on
        self.font = pygame.font.Font(None, 24)

    def draw(self, screen):
        # Draw the switch background
        if self.is_on:
            pygame.draw.rect(screen, (0, 255, 0), self.rect)
        else:
            pygame.draw.rect(screen, (255, 0, 0), self.rect)

        # Draw the switch label
        label_surface = self.font.render(self.label, True, (0, 0, 0))
        screen.blit(label_surface, (self.rect.x + 5, self.rect.y + 5))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.is_on = not self.is_on

class ChatGUI:
    def __init__(self, agents):
        pygame.init()
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Justice Council")

        self.agents = agents
        self.toggle_switches = []
        self.chat_history = []
        self.input_text = ""

        self.font = pygame.font.Font(None, 24)
        self.input_rect = pygame.Rect(10, self.screen_height - 40, self.screen_width - 20, 30)

        self._create_toggle_switches()

    def _create_toggle_switches(self):
        x = 10
        y = 10
        for agent_key, agent in self.agents.items():
            toggle = ToggleSwitch(x, y, 150, 30, agent.profile.name)
            self.toggle_switches.append(toggle)
            x += 160

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                for toggle in self.toggle_switches:
                    toggle.handle_event(event)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        # Handle sending message
                        self.handle_send_message()
                    elif event.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]
                    else:
                        self.input_text += event.unicode

            self.screen.fill((255, 255, 255))
            self._draw_toggle_switches()
            self._draw_chat_history()
            self._draw_input_box()
            pygame.display.flip()

        pygame.quit()

    def _draw_toggle_switches(self):
        for toggle in self.toggle_switches:
            toggle.draw(self.screen)

    def _draw_chat_history(self):
        y = 50
        for message in self.chat_history:
            text_surface = self.font.render(message, True, (0, 0, 0))
            self.screen.blit(text_surface, (10, y))
            y += 20

    def _draw_input_box(self):
        pygame.draw.rect(self.screen, (0, 0, 0), self.input_rect, 2)
        input_surface = self.font.render(self.input_text, True, (0, 0, 0))
        self.screen.blit(input_surface, (self.input_rect.x + 5, self.input_rect.y + 5))

    def handle_send_message(self):
        # This method will be implemented in main.py
        pass
