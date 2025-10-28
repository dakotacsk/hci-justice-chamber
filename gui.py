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
        pygame.key.set_repeat(300, 30)
        self.screen_width = 1560
        self.screen_height = 878
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Justice Council")

        # Background
        self.background_image = pygame.image.load("resources/background.jpg")
        self.background_image = pygame.transform.scale(
            self.background_image, (self.screen_width, self.screen_height)
        )

        # Dialogue box
        self.dialogue_box_image = pygame.image.load("resources/dialogue_box.jpg")
        self.dialogue_box_image = pygame.transform.scale(
            self.dialogue_box_image, (self.screen_width * 0.8, 150)
        )

        # Dialogue box text
        self.dialogue_box_rect = pygame.Rect(300, 700, 1080, 125)

        # Text box setup
        self.input_box = pygame.Rect(
            1560 - 40 - 500,
            40,
            500,
            int(self.screen_height * 0.2),
        )
        self.color = (150, 150, 150)
        self.active = False
        self.text = ""

        # Character Sprites
        self.meritocracy = pygame.image.load("resources/sprites/meritocracy.jpg")
        self.meritocracy = pygame.transform.scale(self.meritocracy, (60, 100))
        self.restorative = pygame.image.load("resources/sprites/restorative.jpg")
        self.restorative = pygame.transform.scale(self.restorative, (60, 100))
        self.rawlsian = pygame.image.load("resources/sprites/rawlsian.jpg")
        self.rawlsian = pygame.transform.scale(self.rawlsian, (60, 100))
        self.utilitarian = pygame.image.load("resources/sprites/utilitarian.jpg")
        self.utilitarian = pygame.transform.scale(self.utilitarian, (60, 100))

        self.agents = agents
        self.toggle_switches = []
        self.action_history = []
        self.chat_history = []
        self.input_text = ""

        self.font = pygame.font.Font(None, 24)
        self.input_rect = pygame.Rect(
            10, self.screen_height - 40, self.screen_width - 20, 30
        )

        self._create_toggle_switches()

    def _create_toggle_switches(self):
        x = 40
        y = 40
        for agent_key, agent in self.agents.items():
            toggle = ToggleSwitch(x, y, 150, 30, agent.profile.name)
            self.toggle_switches.append(toggle)
            x += 160

    def draw_background(self):
        self.screen.blit(self.background_image, (0, 0))

    def draw_dialogue_box(self):
        self.screen.blit(self.dialogue_box_image, (self.screen_width * 0.1, 675))
        if len(self.chat_history) != 0:
            self.render_wrapped_text(
                self.chat_history[-1],
                self.font,
                (0, 0, 0),
                self.dialogue_box_rect,
                self.screen,
            )

    def draw_sprite(self):
        for toggle in self.toggle_switches:
            match toggle.label:
                case "Dr. Sam Iqbal":
                    if toggle.is_on:
                        self.screen.blit(self.utilitarian, (760, 530))
                case "Amara Ndlovu":
                    if toggle.is_on:
                        self.screen.blit(self.restorative, (860, 415))
                case "Jamie Reyes":
                    if toggle.is_on:
                        self.screen.blit(self.meritocracy, (650, 415))
                case "Jordan Chex":
                    if toggle.is_on:
                        self.screen.blit(self.rawlsian, (760, 305))

    def draw_textbox(self):
        self.color = (0, 0, 0) if self.active else (150, 150, 150)
        pygame.draw.rect(self.screen, self.color, self.input_box, 2)
        self.render_wrapped_text(
            self.text, self.font, self.color, self.input_box, self.screen
        )

    def _draw_toggle_switches(self):
        for toggle in self.toggle_switches:
            toggle.draw(self.screen)

    def _draw_action_history(self):
        y = 100
        for message in self.action_history:
            text_surface = self.font.render(message, True, (0, 0, 0))
            self.screen.blit(text_surface, (47, y))
            y += 20

    def render_wrapped_text(self, text, font, color, rect, surface):
        """
        Render text into `rect` on `surface`, wrapping words and handling '\n'.
        - text: string
        - font: pygame.font.Font
        - color: (r,g,b)
        - rect: pygame.Rect (target box)
        - surface: pygame.Surface
        - padding: inner padding in px
        Returns: total vertical pixels used (so caller can decide about scrolling)
        """
        padding = 10
        x = rect.x + padding
        y = rect.y + padding
        max_width = rect.width - 2 * padding
        line_height = font.get_linesize()

        # Split input into paragraphs on explicit newline
        paragraphs = text.split("\n")
        total_height_used = 0

        for p_i, para in enumerate(paragraphs):
            # split paragraph into words (preserve multiple spaces by splitting and rejoining)
            words = para.split(" ")
            line = ""

            for w_i, word in enumerate(words):
                # If line is empty, candidate is the word; else include a leading space
                candidate = word if line == "" else line + " " + word
                candidate_width = font.size(candidate)[0]

                if candidate_width <= max_width:
                    # fits on current line
                    line = candidate
                else:
                    # candidate doesn't fit. If current line is not empty, draw it and start a new line
                    if line != "":
                        # draw current line
                        if y + line_height > rect.bottom - padding:
                            return total_height_used  # can't draw more — clipped
                        surface.blit(font.render(line, True, color), (x, y))
                        y += line_height
                        total_height_used += line_height
                        line = word  # start new line with the word
                        # If word itself is longer than max_width, we must split the word
                        if font.size(line)[0] > max_width:
                            # split word into characters to fill line-by-line
                            part = ""
                            for ch in line:
                                if font.size(part + ch)[0] <= max_width:
                                    part += ch
                                else:
                                    # draw part
                                    if y + line_height > rect.bottom - padding:
                                        return total_height_used
                                    surface.blit(font.render(part, True, color), (x, y))
                                    y += line_height
                                    total_height_used += line_height
                                    part = ch
                            # remaining part becomes the new current line
                            line = part
                    else:
                        # line is empty but the word itself is too long; split characters
                        part = ""
                        for ch in word:
                            if font.size(part + ch)[0] <= max_width:
                                part += ch
                            else:
                                if y + line_height > rect.bottom - padding:
                                    return total_height_used
                                surface.blit(font.render(part, True, color), (x, y))
                                y += line_height
                                total_height_used += line_height
                                part = ch
                        line = part

            # end for words -> draw remaining line for this paragraph
            if line != "":
                if y + line_height > rect.bottom - padding:
                    return total_height_used
                surface.blit(font.render(line, True, color), (x, y))
                y += line_height
                total_height_used += line_height

            # After each paragraph except the last, force a blank line (honor '\n')
            if p_i != len(paragraphs) - 1:
                # add one blank line-height
                if y + line_height > rect.bottom - padding:
                    return total_height_used
                y += line_height
                total_height_used += line_height

        return total_height_used
