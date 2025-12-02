import pygame
import pygame_gui
import time

# --- UI Components ---


class Button:
    """Wrapper for pygame-gui UIButton to maintain compatibility"""
    def __init__(self, x, y, width, height, label, manager, color=(100, 100, 200)):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.color = color
        self.button = pygame_gui.elements.UIButton(
            relative_rect=self.rect,
            text=label,
            manager=manager
        )
        # Set custom colors
        self.button.colours['normal_bg'] = color
        self.button.colours['hovered_bg'] = tuple(min(255, c + 20) for c in color)
        self.button.colours['pressed_bg'] = tuple(max(0, c - 20) for c in color)

    def draw(self, screen):
        # pygame-gui handles drawing automatically
        pass

    def is_clicked(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.button:
                return True
        return False


class CheckBox:
    """Wrapper for pygame-gui UICheckBox to maintain compatibility"""
    def __init__(self, x, y, width, height, label, manager, is_on=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.checkbox = pygame_gui.elements.UICheckBox(
            relative_rect=self.rect,
            text="",  # Empty text since we draw label separately
            manager=manager
        )
        # Track state ourselves since pygame-gui UICheckBox state can be tricky
        self._checked = is_on
        if is_on:
            try:
                self.checkbox.checked = True
            except:
                pass
        # Create label text separately
        self.label_surface = pygame.font.Font("resources/roboto_fonts/Roboto-Regular.ttf", int(24 * 0.8)).render(
            label, True, (255, 255, 255)
        )
        self.label_pos = (self.rect.x + self.rect.width + 10, self.rect.y)

    def draw(self, screen):
        # pygame-gui handles checkbox drawing, but we draw the label
        screen.blit(self.label_surface, self.label_pos)

    @property
    def is_on(self):
        # Try multiple methods to check state
        try:
            # First try the checked attribute
            if hasattr(self.checkbox, 'checked'):
                checked = self.checkbox.checked
                self._checked = bool(checked)
                return self._checked
        except:
            pass
        
        # Try get_state()
        try:
            state = self.checkbox.get_state()
            # UICheckBox states: when checked, might be 'selected' or contain 'selected'
            if 'selected' in str(state).lower():
                self._checked = True
                return True
        except:
            pass
        
        # Fallback to our tracked state
        return self._checked

    @is_on.setter
    def is_on(self, value):
        self._checked = bool(value)
        try:
            self.checkbox.checked = self._checked
        except:
            pass

    def handle_event(self, event):
        # Listen for checkbox state changes
        if event.type == pygame_gui.UI_CHECK_BOX_CHECKED:
            if event.ui_element == self.checkbox:
                self._checked = True
        elif event.type == pygame_gui.UI_CHECK_BOX_UNCHECKED:
            if event.ui_element == self.checkbox:
                self._checked = False
        return False


class TextInputBox:
    """Multi-line text input using UITextBox with manual editing support"""
    def __init__(self, x, y, width, height, font, manager, placeholder=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.placeholder = placeholder
        self.font = font
        self.active = False
        
        # Use UITextBox for display with scrollbars
        # Set placeholder as initial HTML if provided
        initial_html = ""
        if placeholder:
            initial_html = f'<body bgcolor="#FFFFFF"><font color="#999999">{placeholder}</font></body>'
        self.textbox = pygame_gui.elements.UITextBox(
            relative_rect=self.rect,
            html_text=initial_html,
            manager=manager,
            wrap_to_height=True
        )
        # Try to make background transparent/white by setting all possible color properties
        white = pygame.Color(255, 255, 255)
        black = pygame.Color(0, 0, 0)
        if hasattr(self.textbox, 'colours'):
            # Set all background-related colors to white
            for bg_key in ['dark_bg', 'normal_bg', 'selected_bg', 'bg', 'background_colour', 'misc_bg']:
                if bg_key in self.textbox.colours:
                    self.textbox.colours[bg_key] = white
            # Set text colors to black
            for text_key in ['normal_text', 'text', 'text_colour', 'text_color']:
                if text_key in self.textbox.colours:
                    self.textbox.colours[text_key] = black
        # Also try setting background_colour attribute directly if it exists
        if hasattr(self.textbox, 'background_colour'):
            self.textbox.background_colour = white
        self.textbox.rebuild()
        
        # Store text separately
        self._text = ""
        self._lines = [""]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.active = True
            else:
                self.active = False

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                if self._lines[-1]:
                    self._lines[-1] = self._lines[-1][:-1]
                elif len(self._lines) > 1:
                    self._lines.pop()
            elif event.key == pygame.K_RETURN:
                self._lines.append("")
            else:
                if event.unicode:
                    self._lines[-1] += event.unicode
            self._text = "\n".join(self._lines)
            # Update the textbox - escape HTML and convert newlines
            if self._text:
                escaped_msg = self._text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
                html_text = f'<body bgcolor="#FFFFFF"><font color="#000000">{escaped_msg}</font></body>'
            else:
                # Show placeholder if text is empty
                html_text = f'<body bgcolor="#FFFFFF"><font color="#999999">{self.placeholder}</font></body>' if self.placeholder else '<body bgcolor="#FFFFFF"></body>'
            self.textbox.html_text = html_text
            self.textbox.rebuild()
            # Ensure white background after rebuild - try all possible keys
            if hasattr(self.textbox, 'colours'):
                white = pygame.Color(255, 255, 255)
                for bg_key in ['dark_bg', 'normal_bg', 'selected_bg', 'bg', 'background_colour', 'misc_bg']:
                    if bg_key in self.textbox.colours:
                        self.textbox.colours[bg_key] = white

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        self._lines = value.split("\n") if value else [""]
        if value:
            escaped_msg = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
            html_text = f'<body bgcolor="#FFFFFF"><font color="#000000">{escaped_msg}</font></body>'
        else:
            # Show placeholder if text is empty
            html_text = f'<body bgcolor="#FFFFFF"><font color="#999999">{self.placeholder}</font></body>' if self.placeholder else '<body bgcolor="#FFFFFF"></body>'
        self.textbox.html_text = html_text
        self.textbox.rebuild()
        # Ensure white background after rebuild
        if hasattr(self.textbox, 'colours'):
            white = pygame.Color(255, 255, 255)
            for bg_key in ['dark_bg', 'normal_bg', 'selected_bg', 'bg']:
                if bg_key in self.textbox.colours:
                    self.textbox.colours[bg_key] = white

    def clear(self):
        self.text = ""
        self._lines = [""]

    def draw(self, screen):
        # Draw white background rectangle - this will be drawn before pygame-gui renders
        # Fill the entire rect with white to cover any grey background
        pygame.draw.rect(screen, (255, 255, 255), self.rect)
        # Draw a subtle border
        pygame.draw.rect(screen, (220, 220, 220), self.rect, width=1)


# --- Main UI Views ---


class CreationForm:
    def __init__(self, screen_width, screen_height):
        self.manager = pygame_gui.UIManager((screen_width, screen_height))
        self.font_title = pygame.font.Font("resources/roboto_fonts/Roboto-Bold.ttf", int(48 * 0.8))
        self.font_label = pygame.font.Font("resources/roboto_fonts/Roboto-Regular.ttf", int(32 * 0.8))
        self.font_input = pygame.font.Font("resources/roboto_fonts/Roboto-Regular.ttf", int(28 * 0.8))
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
        input_h = int(35 * 0.8)
        start_y = int(150 * 0.8)
        y_padding = int(100 * 0.8)

        for i, q in enumerate(self.questions):
            y_pos = start_y + i * y_padding
            label_surface = self.font_label.render(q, True, (255, 255, 255))  # White text for dark blue background
            self.labels.append((label_surface, (self.width / 2 - input_w / 2, y_pos)))
            
            # Use TextInputBox for multi-line input with scrollbars
            box_rect = pygame.Rect(
                self.width / 2 - input_w / 2,
                y_pos + int(40 * 0.8),
                input_w,
                input_h
            )
            textbox = TextInputBox(
                box_rect.x, box_rect.y, box_rect.width, box_rect.height,
                self.font_input, self.manager
            )
            self.input_boxes.append(textbox)

        save_rect = pygame.Rect(
            self.width / 2 - int(100 * 0.8),
            start_y + len(self.questions) * y_padding,
            int(200 * 0.8),
            int(50 * 0.8)
        )
        self.save_button = Button(
            save_rect.x, save_rect.y, save_rect.width, save_rect.height,
            "Save Advocate", self.manager
        )
        
        back_rect = pygame.Rect(
            int(20 * 0.8),
            int(20 * 0.8),
            int(40 * 0.8),
            int(40 * 0.8)
        )
        self.back_button = Button(
            back_rect.x, back_rect.y, back_rect.width, back_rect.height,
            "<", self.manager
        )

    def handle_event(self, event):
        self.manager.process_events(event)
        
        for box in self.input_boxes:
            box.handle_event(event)
            
        if self.save_button.is_clicked(event):
            return {
                "name": self.input_boxes[0].text,
                "definition": self.input_boxes[1].text,
                "values": self.input_boxes[2].text,
                "tone": self.input_boxes[3].text,
            }
        if self.back_button.is_clicked(event):
            return "back"
        return None

    def draw(self, screen):
        screen.fill((20, 20, 40))  # Dark blue background
        title_surface = self.font_title.render(
            "Create Your Justice Advocate", True, (255, 255, 255)  # White text
        )
        screen.blit(title_surface, (self.width / 2 - title_surface.get_width() / 2, int(50 * 0.8)))

        for label, pos in self.labels:
            screen.blit(label, pos)
        # Draw white backgrounds for input boxes before pygame-gui renders
        for box in self.input_boxes:
            box.draw(screen)

        self.save_button.draw(screen)
        self.back_button.draw(screen)
        
        self.manager.update(pygame.time.get_ticks() / 1000.0)
        self.manager.draw_ui(screen)
        
        # Draw white rectangles over text boxes AFTER pygame-gui renders
        # This will cover the grey background, but we need to preserve text
        # Since pygame-gui renders text as part of the element, we'll need to re-draw text
        # Actually, let's try a simpler approach: just ensure our pre-draw white rectangles are working
        # The grey might be coming from pygame-gui's default theme
        # Let's try drawing white with a special blend mode that preserves text colors
        for box in self.input_boxes:
            # Draw white rectangle - this will cover grey but also text
            # We'll need to re-render the text content
            pygame.draw.rect(screen, (255, 255, 255), box.rect)
            pygame.draw.rect(screen, (220, 220, 220), box.rect, width=1)
            # Re-render text content on top
            if box._text:
                # Render text manually on top of white background
                y_offset = box.rect.y + 5
                for line in box._lines:
                    if line:
                        text_surface = box.font.render(line, True, (0, 0, 0))
                        screen.blit(text_surface, (box.rect.x + 5, y_offset))
                    y_offset += box.font.get_linesize()
            elif box.placeholder:
                # Render placeholder
                placeholder_surface = box.font.render(box.placeholder, True, (150, 150, 150))
                screen.blit(placeholder_surface, (box.rect.x + 5, box.rect.y + 5))


class ChatGUI:
    def __init__(self, agents, screen_width, screen_height, selected_advocate_key=None, num_custom_advocates=0):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.manager = pygame_gui.UIManager((screen_width, screen_height))
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Justice Council")

        # Resources
        self.background_image = pygame.image.load("resources/background.jpg").convert()
        self.background_image = pygame.transform.scale(
            self.background_image, (self.screen_width, self.screen_height)
        )
        self.dialogue_box_rect = pygame.Rect(int(300 * 0.8), int(700 * 0.8), int(1080 * 0.8), int(125 * 0.8))

        # Sprites
        self.sprites = {
            "Dr. Sam Iqbal": pygame.transform.scale(
                pygame.image.load("resources/sprites/utilitarian.png").convert_alpha(),
                (int(60 * 0.8), int(100 * 0.8)),
            ),
            "Amara Ndlovu": pygame.transform.scale(
                pygame.image.load("resources/sprites/restorative.png").convert_alpha(),
                (int(60 * 0.8), int(100 * 0.8)),
            ),
            "Jamie Reyes": pygame.transform.scale(
                pygame.image.load("resources/sprites/meritocracy.png").convert_alpha(),
                (int(60 * 0.8), int(100 * 0.8)),
            ),
            "Jordan Chex": pygame.transform.scale(
                pygame.image.load("resources/sprites/rawlsian.png").convert_alpha(),
                (int(60 * 0.8), int(100 * 0.8)),
            ),
        }

        # State & UI
        self.font = pygame.font.Font("resources/roboto_fonts/Roboto-Regular.ttf", int(24 * 0.8))
        self.agents = agents
        self.chat_history = [
            "Please select who you would want to talk to...",
        ]
        self.current_chat_index = 0
        self._last_displayed_index = -1
        
        # Create chat display textbox with scrollbars
        self.chat_display = pygame_gui.elements.UITextBox(
            relative_rect=self.dialogue_box_rect,
            html_text="Please select who you would want to talk to...",
            manager=self.manager,
            wrap_to_height=True
        )
        # Ensure white background for chat display
        # UITextBox uses 'dark_bg' for the main background color
        if hasattr(self.chat_display, 'colours'):
            white = pygame.Color(255, 255, 255)
            black = pygame.Color(0, 0, 0)
            # Set background to white - try all possible background color keys
            for bg_key in ['dark_bg', 'normal_bg', 'selected_bg', 'bg']:
                if bg_key in self.chat_display.colours:
                    self.chat_display.colours[bg_key] = white
            # Set text color to black
            for text_key in ['normal_text', 'text', 'text_colour']:
                if text_key in self.chat_display.colours:
                    self.chat_display.colours[text_key] = black
            # Force rebuild to apply colors
            self.chat_display.rebuild()
        self._update_chat_display()
        
        input_box_x = int((1560 - 40 - 500) * 0.8)
        input_box_y = int(40 * 0.8)
        input_box_width = int(500 * 0.8)
        input_box_height = int(self.screen_height * 0.2)
        
        input_rect = pygame.Rect(input_box_x, input_box_y, input_box_width, input_box_height)
        self.main_input_box = TextInputBox(
            input_box_x, input_box_y, input_box_width, input_box_height,
            pygame.font.Font("resources/roboto_fonts/Roboto-Regular.ttf", int(24 * 0.8)),
            self.manager,
            placeholder="(ask a question or tell a story about justice...)"
        )
        
        submit_rect = pygame.Rect(
            input_box_x + input_box_width - int(120 * 0.8),
            input_box_y + input_box_height + int(10 * 0.8),
            int(120 * 0.8),
            int(40 * 0.8)
        )
        self.submit_button = Button(
            submit_rect.x, submit_rect.y, submit_rect.width, submit_rect.height,
            "Submit", self.manager
        )
        
        create_rect = pygame.Rect(
            self.screen_width - int(220 * 0.8),
            self.screen_height - int(60 * 0.8),
            int(200 * 0.8),
            int(40 * 0.8)
        )
        self.create_advocate_button = Button(
            create_rect.x, create_rect.y, create_rect.width, create_rect.height,
            "Create Advocate", self.manager
        )
        
        prev_rect = pygame.Rect(
            self.dialogue_box_rect.x - int(60 * 0.8),
            self.dialogue_box_rect.centery - int(20 * 0.8),
            int(50 * 0.8),
            int(40 * 0.8)
        )
        self.prev_button = Button(
            prev_rect.x, prev_rect.y, prev_rect.width, prev_rect.height,
            "<", self.manager
        )
        
        next_rect = pygame.Rect(
            self.dialogue_box_rect.right + int(10 * 0.8),
            self.dialogue_box_rect.centery - int(20 * 0.8),
            int(50 * 0.8),
            int(40 * 0.8)
        )
        self.next_button = Button(
            next_rect.x, next_rect.y, next_rect.width, next_rect.height,
            ">", self.manager
        )
        
        self.checkboxes = self._create_checkboxes()
        self.checkbox_label = pygame.font.Font("resources/roboto_fonts/Roboto-Regular.ttf", int(24 * 0.8)).render(
            "Select the character(s) you would like to talk to:", True, (20, 20, 20)  # Black text for visibility
        )

    def _create_checkboxes(self):
        checkboxes = []
        x, y = int(40 * 0.8), int(80 * 0.8)
        for agent in self.agents.values():
            checkbox_rect = pygame.Rect(x, y, int(20 * 0.8), int(20 * 0.8))
            checkbox = CheckBox(
                checkbox_rect.x, checkbox_rect.y, checkbox_rect.width, checkbox_rect.height,
                agent.profile.name, self.manager
            )
            checkboxes.append(checkbox)
            y += int(40 * 0.8)
        return checkboxes

    def handle_event(self, event):
        self.manager.process_events(event)
        
        self.main_input_box.handle_event(event)
        for checkbox in self.checkboxes:
            checkbox.handle_event(event)

        if self.prev_button.is_clicked(event):
            if self.current_chat_index > 0:
                self.current_chat_index -= 1
                while self.current_chat_index > 0 and self.chat_history[self.current_chat_index].startswith("You:"):
                    self.current_chat_index -= 1
                self._update_chat_display()
                
        if self.next_button.is_clicked(event):
            if self.current_chat_index < len(self.chat_history) - 1:
                self.current_chat_index += 1
                while self.current_chat_index < len(self.chat_history) - 1 and self.chat_history[self.current_chat_index].startswith("You:"):
                    self.current_chat_index += 1
                self._update_chat_display()

    def _update_chat_display(self):
        if self.chat_history and 0 <= self.current_chat_index < len(self.chat_history):
            # Only update if index changed
            if self._last_displayed_index != self.current_chat_index:
                message = self.chat_history[self.current_chat_index]
                # Escape HTML and convert newlines, wrap in div with white background and black text
                escaped_msg = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
                html_text = f'<body bgcolor="#FFFFFF"><font color="#000000">{escaped_msg}</font></body>'
                self.chat_display.html_text = html_text
                self.chat_display.rebuild()
                # Set colors after rebuild to ensure they're applied
                if hasattr(self.chat_display, 'colours'):
                    white = pygame.Color(255, 255, 255)
                    for bg_key in ['dark_bg', 'normal_bg', 'selected_bg', 'bg']:
                        if bg_key in self.chat_display.colours:
                            self.chat_display.colours[bg_key] = white
                # Reset scroll position to top when displaying new message
                if hasattr(self.chat_display, 'scroll_bar') and self.chat_display.scroll_bar is not None:
                    self.chat_display.scroll_bar.set_scroll_from_start_percentage(0.0)
                self._last_displayed_index = self.current_chat_index

    def draw(self, screen):
        screen.blit(self.background_image, (0, 0))

        # Update chat display if index changed (e.g., when new messages are added)
        self._update_chat_display()

        self.prev_button.draw(screen)
        self.next_button.draw(screen)

        self.main_input_box.draw(screen)
        self.submit_button.draw(screen)
        self.create_advocate_button.draw(screen)
        
        screen.blit(self.checkbox_label, (int(40 * 0.8), int(40 * 0.8)))
        for checkbox in self.checkboxes:
            checkbox.draw(screen)

        self._draw_sprites(screen)
        
        # Draw white backgrounds before pygame-gui renders
        # Draw white background for chat display
        pygame.draw.rect(screen, (255, 255, 255), self.dialogue_box_rect)
        pygame.draw.rect(screen, (200, 200, 200), self.dialogue_box_rect, width=2)
        
        self.manager.update(pygame.time.get_ticks() / 1000.0)
        self.manager.draw_ui(screen)

    def _get_sprite_pos(self, agent_name):
        sprite_positions = {
            "Dr. Sam Iqbal": (int(760 * 0.8), int(530 * 0.8)),
            "Amara Ndlovu": (int(860 * 0.8), int(415 * 0.8)),
            "Jamie Reyes": (int(650 * 0.8), int(415 * 0.8)),
            "Jordan Chex": (int(760 * 0.8), int(305 * 0.8)),
        }
        return sprite_positions.get(agent_name)

    def _draw_sprites(self, screen):
        for checkbox in self.checkboxes:
            if checkbox.is_on and checkbox.label in self.sprites:
                sprite_pos = self._get_sprite_pos(checkbox.label)
                if sprite_pos:
                    screen.blit(self.sprites[checkbox.label], sprite_pos)


class AdvocateSelectionScreen:
    def __init__(self, screen_width, screen_height, custom_advocates):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.manager = pygame_gui.UIManager((screen_width, screen_height))
        self.custom_advocates = custom_advocates
        
        self.font_title = pygame.font.Font("resources/roboto_fonts/Roboto-Bold.ttf", int(48 * 0.8))
        self.font_label = pygame.font.Font("resources/roboto_fonts/Roboto-Regular.ttf", int(32 * 0.8))
        
        # Create buttons for each advocate
        self.advocate_buttons = []
        start_y = int(150 * 0.8)
        button_height = int(50 * 0.8)
        button_width = int(400 * 0.8)
        y_padding = int(70 * 0.8)
        
        for i, advocate in enumerate(custom_advocates):
            button_rect = pygame.Rect(
                self.screen_width / 2 - button_width / 2,
                start_y + i * y_padding,
                button_width,
                button_height
            )
            button = Button(
                button_rect.x, button_rect.y, button_rect.width, button_rect.height,
                advocate.name, self.manager
            )
            button.advocate_name = advocate.name  # Store name for identification
            self.advocate_buttons.append(button)
        
        # Back button
        back_rect = pygame.Rect(
            int(20 * 0.8),
            int(20 * 0.8),
            int(100 * 0.8),
            int(40 * 0.8)
        )
        self.back_button = Button(
            back_rect.x, back_rect.y, back_rect.width, back_rect.height,
            "Back", self.manager
        )

    def handle_event(self, event):
        self.manager.process_events(event)
        
        if self.back_button.is_clicked(event):
            return "back"
        
        for button in self.advocate_buttons:
            if button.is_clicked(event):
                return button.advocate_name
        
        return None

    def draw(self, screen):
        screen.fill((255, 255, 255))  # White background
        
        title_surface = self.font_title.render(
            "Select an Advocate", True, (20, 20, 20)  # Black text
        )
        screen.blit(title_surface, (self.screen_width / 2 - title_surface.get_width() / 2, int(50 * 0.8)))
        
        for button in self.advocate_buttons:
            button.draw(screen)
        
        self.back_button.draw(screen)
        
        self.manager.update(pygame.time.get_ticks() / 1000.0)
        self.manager.draw_ui(screen)
