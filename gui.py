import pygame
import time

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
    def __init__(self, x, y, width, height, label, is_on=False):
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
    def __init__(self, x, y, width, height, font, placeholder=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = ""
        self.placeholder = placeholder
        self.font = font
        self.active = False
        self.color_active = pygame.Color("dodgerblue2")
        self.color_inactive = pygame.Color("lightgray")
        self.color = self.color_inactive
        self.lines = [""]
        self.scroll_offset = 0
        self.line_height = font.get_linesize()
        self.scrollbar_width = 15
        self.dragging_scrollbar = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.active = True
                self.color = self.color_active
                scrollbar_rect = self._get_scrollbar_rect()
                if scrollbar_rect and scrollbar_rect.collidepoint(event.pos):
                    self.dragging_scrollbar = True
            else:
                self.active = False
                self.color = self.color_inactive

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_scrollbar = False

        if event.type == pygame.MOUSEMOTION and self.dragging_scrollbar:
            mouse_y = event.pos[1]
            thumb_rect = self._get_thumb_rect()
            if thumb_rect:
                content_height = len(self.lines) * self.line_height
                if content_height > self.rect.height:
                    scrollable_height = self.rect.height - thumb_rect.height
                    if scrollable_height > 0:
                        ratio = (mouse_y - self.rect.y - thumb_rect.height / 2) / scrollable_height
                        self.scroll_offset = ratio * (len(self.lines) - self.rect.height / self.line_height)
                        self._clamp_scroll()

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                if self.lines[-1]:
                    self.lines[-1] = self.lines[-1][:-1]
                elif len(self.lines) > 1:
                    self.lines.pop()
            elif event.key == pygame.K_RETURN:
                self.lines.append("")
            else:
                self.lines[-1] += event.unicode
                self._wrap_text()
            self.text = "\n".join(self.lines)

        if event.type == pygame.MOUSEWHEEL and self.active:
            self.scroll_offset -= event.y
            self._clamp_scroll()

    def _clamp_scroll(self):
        max_scroll = max(0, len(self.lines) - int(self.rect.height / self.line_height))
        if self.scroll_offset < 0:
            self.scroll_offset = 0
        if self.scroll_offset > max_scroll:
            self.scroll_offset = max_scroll

    def _wrap_text(self):
        max_width = self.rect.width - 10 - self.scrollbar_width
        while self.font.size(self.lines[-1])[0] > max_width:
            line = self.lines[-1]
            split_pos = -1
            for i in range(len(line) - 1, 0, -1):
                if line[i] == ' ':
                    split_pos = i
                    break
            if split_pos != -1:
                self.lines[-1] = line[:split_pos]
                self.lines.append(line[split_pos+1:])
            else:
                # No space found, just break the line
                self.lines.append(self.lines[-1][-1])
                self.lines[-2] = self.lines[-2][:-1]

    def _get_scrollbar_rect(self):
        return pygame.Rect(self.rect.right - self.scrollbar_width, self.rect.y, self.scrollbar_width, self.rect.height)

    def _get_thumb_rect(self):
        content_height = len(self.lines) * self.line_height
        if content_height > self.rect.height:
            thumb_height = self.rect.height * (self.rect.height / content_height)
            scrollable_range = content_height - self.rect.height
            if scrollable_range > 0:
                thumb_y = self.rect.y + (self.scroll_offset * self.line_height) * (self.rect.height - thumb_height) / scrollable_range
                return pygame.Rect(self.rect.right - self.scrollbar_width, thumb_y, self.scrollbar_width, thumb_height)
        return None

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 255, 255), self.rect)
        pygame.draw.rect(screen, self.color, self.rect, 2)

        if not self.text and self.placeholder:
            placeholder_surface = self.font.render(self.placeholder, True, (150, 150, 150))
            screen.blit(placeholder_surface, (self.rect.x + 5, self.rect.y + 5))
            return

        y = self.rect.y + 5 - self.scroll_offset * self.line_height
        for line in self.lines:
            if y + self.line_height > self.rect.y and y < self.rect.bottom:
                text_surface = self.font.render(line, True, (0, 0, 0))
                screen.blit(text_surface, (self.rect.x + 5, y))
            y += self.line_height

        scrollbar_rect = self._get_scrollbar_rect()
        if scrollbar_rect:
            pygame.draw.rect(screen, (230, 230, 230), scrollbar_rect)
            thumb_rect = self._get_thumb_rect()
            if thumb_rect:
                pygame.draw.rect(screen, (180, 180, 180), thumb_rect)


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
            box = TextInputBox(
                self.width / 2 - input_w / 2,
                y_pos + 40,
                input_w,
                input_h,
                self.font_input,
            )
            self.input_boxes.append(box)

        self.save_button = Button(
            self.width / 2 - 100,
            start_y + len(self.questions) * y_padding,
            200,
            50,
            "Save Advocate",
        )

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
        screen.fill((20, 20, 40))  # Dark blue background
        title_surface = self.font_title.render(
            "Create Your Justice Advocate", True, (255, 255, 255)
        )
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
        self.background_image = pygame.transform.scale(
            self.background_image, (self.screen_width, self.screen_height)
        )
        self.dialogue_box_image = pygame.image.load(
            "resources/dialogue_box.jpg"
        ).convert_alpha()
        self.dialogue_box_image = pygame.transform.scale(
            self.dialogue_box_image, (self.screen_width * 0.8, 150)
        )
        self.dialogue_box_rect = pygame.Rect(300, 700, 1080, 125)

        # Sprites
        self.sprites = {
            "Dr. Sam Iqbal": pygame.transform.scale(
                pygame.image.load("resources/sprites/utilitarian.png").convert_alpha(),
                (60, 100),
            ),
            "Amara Ndlovu": pygame.transform.scale(
                pygame.image.load("resources/sprites/restorative.png").convert_alpha(),
                (60, 100),
            ),
            "Jamie Reyes": pygame.transform.scale(
                pygame.image.load("resources/sprites/meritocracy.png").convert_alpha(),
                (60, 100),
            ),
            "Jordan Chex": pygame.transform.scale(
                pygame.image.load("resources/sprites/rawlsian.png").convert_alpha(),
                (60, 100),
            ),
        }

        # State & UI
        self.font = pygame.font.Font(None, 24)
        self.agents = agents
        self.chat_history = [
            "Please select who you would want to talk to...",
        ]
        self.chat_scroll_offset = 0
        self.chat_scrollbar_width = 15
        self.dragging_chat_scrollbar = False
        input_box_x = 1560 - 40 - 500
        input_box_y = 40
        input_box_width = 500
        input_box_height = int(self.screen_height * 0.2)
        
        self.main_input_box = TextInputBox(
            input_box_x, input_box_y, input_box_width, input_box_height, self.font, placeholder="(type here...)"
        )
        self.submit_button = Button(
            input_box_x + input_box_width - 120, input_box_y + input_box_height + 10, 120, 40, "Submit"
        )
        self.create_advocate_button = Button(
            self.screen_width - 220, self.screen_height - 60, 200, 40, "Create Advocate"
        )
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

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            chat_scrollbar_rect = self._get_chat_scrollbar_rect()
            if chat_scrollbar_rect and chat_scrollbar_rect.collidepoint(event.pos):
                self.dragging_chat_scrollbar = True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_chat_scrollbar = False

        if event.type == pygame.MOUSEMOTION and self.dragging_chat_scrollbar:
            mouse_y = event.pos[1]
            thumb_rect = self._get_chat_thumb_rect()
            if thumb_rect:
                content_height = self._get_chat_content_height()
                if content_height > self.dialogue_box_rect.height:
                    scrollable_height = self.dialogue_box_rect.height - thumb_rect.height
                    ratio = (mouse_y - self.dialogue_box_rect.y - thumb_rect.height / 2) / scrollable_height
                    self.chat_scroll_offset = ratio * (content_height - self.dialogue_box_rect.height)
                    self._clamp_chat_scroll()

        if event.type == pygame.MOUSEWHEEL:
            self.chat_scroll_offset -= event.y * 10
            self._clamp_chat_scroll()

    def _clamp_chat_scroll(self):
        content_height = self._get_chat_content_height()
        max_scroll = max(0, content_height - self.dialogue_box_rect.height)
        if self.chat_scroll_offset < 0:
            self.chat_scroll_offset = 0
        if self.chat_scroll_offset > max_scroll:
            self.chat_scroll_offset = max_scroll

    def _get_chat_content_height(self):
        if not self.chat_history:
            return 0
        return render_wrapped_text(self.chat_history[-1], self.font, (0,0,0), self.dialogue_box_rect, self.screen, get_height=True)

    def _get_chat_scrollbar_rect(self):
        return pygame.Rect(self.dialogue_box_rect.right - self.chat_scrollbar_width, self.dialogue_box_rect.y, self.chat_scrollbar_width, self.dialogue_box_rect.height)

    def _get_chat_thumb_rect(self):
        content_height = self._get_chat_content_height()
        if content_height > self.dialogue_box_rect.height:
            thumb_height = self.dialogue_box_rect.height * (self.dialogue_box_rect.height / content_height)
            scrollable_range = content_height - self.dialogue_box_rect.height
            if scrollable_range > 0:
                thumb_y = self.dialogue_box_rect.y + self.chat_scroll_offset * (self.dialogue_box_rect.height - thumb_height) / scrollable_range
                return pygame.Rect(self.dialogue_box_rect.right - self.chat_scrollbar_width, thumb_y, self.chat_scrollbar_width, thumb_height)
        return None

    def draw(self, screen):
        screen.blit(self.background_image, (0, 0))
        screen.blit(self.dialogue_box_image, (self.screen_width * 0.1, 675))

        chat_scrollbar_rect = self._get_chat_scrollbar_rect()
        if chat_scrollbar_rect:
            pygame.draw.rect(screen, (230, 230, 230), chat_scrollbar_rect)
            thumb_rect = self._get_chat_thumb_rect()
            if thumb_rect:
                pygame.draw.rect(screen, (180, 180, 180), thumb_rect)

        if self.chat_history:
            # Display the last message from the history
            last_message = self.chat_history[-1]
            render_wrapped_text(
                last_message,
                self.font,
                (0, 0, 0),
                self.dialogue_box_rect,
                screen,
                self.chat_scroll_offset,
            )

        self.main_input_box.draw(screen)
        self.submit_button.draw(screen)
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


def render_wrapped_text(text, font, color, rect, surface, scroll_offset=0, get_height=False):
    padding = 10
    x, y = rect.x + padding, rect.y + padding - scroll_offset
    max_width = rect.width - 2 * padding
    line_height = font.get_linesize()
    paragraphs = text.split("\n")

    total_height = 0
    for para in paragraphs:
        words = para.split(" ")
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if font.size(candidate)[0] <= max_width:
                line = candidate
            else:
                total_height += line_height
                line = word
        total_height += line_height

    if get_height:
        return total_height

    if scroll_offset < 0:
        scroll_offset = 0
    if total_height > rect.height and scroll_offset > total_height - rect.height:
        scroll_offset = total_height - rect.height

    y = rect.y + padding - scroll_offset

    for para in paragraphs:
        words = para.split(" ")
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if font.size(candidate)[0] <= max_width:
                line = candidate
            else:
                if y + line_height > rect.bottom - padding:
                    return scroll_offset
                if y + line_height > rect.top + padding:
                    surface.blit(font.render(line, True, color), (x, y))
                y += line_height
                line = word
        if line:
            if y + line_height > rect.bottom - padding:
                return scroll_offset
            if y + line_height > rect.top + padding:
                surface.blit(font.render(line, True, color), (x, y))
            y += line_height
    return scroll_offset
