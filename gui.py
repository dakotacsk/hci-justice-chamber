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
            wrap_to_height=False  # Fixed height - scrollbars will appear when content overflows
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
        input_h = int(80 * 0.8)  # Increased height to show more content before scrolling
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
        # Removed dialogue_box_rect - using speech bubbles instead

        # Sprites
        self.sprites = {
            "Sam (Utilitarian)": pygame.transform.scale(
                pygame.image.load("resources/sprites/utilitarian.png").convert_alpha(),
                (int(60 * 0.8), int(100 * 0.8)),
            ),
            "Amara (Restorative)": pygame.transform.scale(
                pygame.image.load("resources/sprites/restorative.png").convert_alpha(),
                (int(60 * 0.8), int(100 * 0.8)),
            ),
            "Jamie (Meritocracy)": pygame.transform.scale(
                pygame.image.load("resources/sprites/meritocracy.png").convert_alpha(),
                (int(60 * 0.8), int(100 * 0.8)),
            ),
            "Jordan (Rawlsian)": pygame.transform.scale(
                pygame.image.load("resources/sprites/rawlsian.png").convert_alpha(),
                (int(60 * 0.8), int(100 * 0.8)),
            ),
        }

        # State & UI
        self.font = pygame.font.Font("resources/roboto_fonts/Roboto-Regular.ttf", int(24 * 0.8))
        self.agents = agents
        self.chat_history = []
        self.current_message_index = -1  # Index of current message being displayed
        self.current_bubble_index_in_round = 0  # Which bubble in the current round we're showing
        self.last_round_size = 0  # Track when round changes to reset bubble index
        self.speech_bubble_height = int(200 * 0.8)  # Increased height for speech bubbles
        self.speech_bubble_scroll_offsets = {}  # Scroll offsets per speaker for long messages
        self.speech_bubble_rects = {}  # Store speech bubble positions per speaker
        self.speech_bubble_scrollbars = {}  # pygame-gui scrollbars per speech bubble
        
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
        
        # Removed prev/next buttons - not needed with speech bubbles
        
        self.checkboxes = self._create_checkboxes()
        self.checkbox_label = pygame.font.Font("resources/roboto_fonts/Roboto-Regular.ttf", int(24 * 0.8)).render(
            "Select the character(s) you would like to talk to:", True, (20, 20, 20)  # Black text for visibility
        )
        
        # Next button will be positioned dynamically next to speech bubble
        # Create it initially, position will be updated when bubble is drawn
        next_button_rect = pygame.Rect(0, 0, int(120 * 0.8), int(35 * 0.8))
        self.next_message_button = Button(
            next_button_rect.x, next_button_rect.y, next_button_rect.width, next_button_rect.height,
            "Next Response", self.manager
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

        # Handle next button for cycling through messages
        if self.next_message_button.is_clicked(event):
            self._next_message()
        
        # Handle scroll wheel for speech bubble scrolling
        if event.type == pygame.MOUSEWHEEL:
            # Check which bubble the mouse is over and scroll that one
            mouse_pos = pygame.mouse.get_pos()
            latest_round = self._get_latest_round_messages()
            for msg in latest_round:
                parts = msg.split(":", 1)
                if len(parts) == 2:
                    speaker = parts[0].strip()
                    if speaker in self.speech_bubble_scrollbars and self.speech_bubble_scrollbars[speaker]:
                        bubble_rect = self.speech_bubble_rects.get(speaker)
                        if bubble_rect and bubble_rect.collidepoint(mouse_pos):
                            # Update scrollbar position via pygame-gui
                            current_scroll = self.speech_bubble_scrollbars[speaker].scroll_position
                            new_scroll = max(0, min(
                                current_scroll - event.y * 20,
                                self.speech_bubble_scrollbars[speaker].bottom_limit
                            ))
                            self.speech_bubble_scrollbars[speaker].scroll_position = new_scroll
                            self.speech_bubble_scroll_offsets[speaker] = new_scroll
                            break

    def _get_current_message(self):
        """Get the current message being displayed"""
        if self.chat_history and 0 <= self.current_message_index < len(self.chat_history):
            return self.chat_history[self.current_message_index]
        return None
    
    def _next_message(self):
        """Cycle to the next bubble in the current round"""
        latest_round = self._get_latest_round_messages()
        
        if not latest_round:
            return
        
        # Reset scroll for current speaker
        if self.current_bubble_index_in_round < len(latest_round):
            current_msg = latest_round[self.current_bubble_index_in_round]
            parts = current_msg.split(":", 1)
            if len(parts) == 2:
                current_speaker = parts[0].strip()
                self.speech_bubble_scroll_offsets[current_speaker] = 0
                if current_speaker in self.speech_bubble_scrollbars and self.speech_bubble_scrollbars[current_speaker]:
                    self.speech_bubble_scrollbars[current_speaker].scroll_position = 0
        
        # Move to next bubble in round
        self.current_bubble_index_in_round += 1
        
        # Wrap around if we've gone past the last bubble
        if self.current_bubble_index_in_round >= len(latest_round):
            self.current_bubble_index_in_round = 0
    
    def _clamp_scroll(self):
        """Clamp scroll offset to valid range"""
        current_msg = self._get_current_message()
        if current_msg and not current_msg.startswith("You:"):
            # Calculate max scroll based on content height
            # This will be calculated in the draw function
            pass

    def draw(self, screen):
        screen.blit(self.background_image, (0, 0))

        # Initialize current message index if needed
        if self.current_message_index < 0 and self.chat_history:
            # Find first agent message
            for i, msg in enumerate(self.chat_history):
                if not msg.startswith("You:"):
                    self.current_message_index = i
                    break

        self.main_input_box.draw(screen)
        self.submit_button.draw(screen)
        self.create_advocate_button.draw(screen)
        self.next_message_button.draw(screen)
        
        screen.blit(self.checkbox_label, (int(40 * 0.8), int(40 * 0.8)))
        for checkbox in self.checkboxes:
            checkbox.draw(screen)

        self._draw_sprites(screen)
        
        # Draw speech bubbles above characters (scrollbar updates handled within _draw_speech_bubble)
        self._draw_speech_bubbles(screen)
        
        self.manager.update(pygame.time.get_ticks() / 1000.0)
        self.manager.draw_ui(screen)

    def _get_sprite_pos(self, agent_name):
        sprite_positions = {
            "Sam (Utilitarian)": (int(760 * 0.8), int(530 * 0.8)),
            "Amara (Restorative)": (int(860 * 0.8), int(415 * 0.8)),
            "Jamie (Meritocracy)": (int(650 * 0.8), int(415 * 0.8)),
            "Jordan (Rawlsian)": (int(760 * 0.8), int(305 * 0.8)),
        }
        return sprite_positions.get(agent_name)

    def _draw_sprites(self, screen):
        for checkbox in self.checkboxes:
            if checkbox.is_on and checkbox.label in self.sprites:
                sprite_pos = self._get_sprite_pos(checkbox.label)
                if sprite_pos:
                    screen.blit(self.sprites[checkbox.label], sprite_pos)

    def _get_latest_round_messages(self):
        """Get all agent messages from the most recent round (after last 'You:' message)"""
        if not self.chat_history:
            return []
        
        # Find the index of the last "You:" message
        last_user_idx = -1
        for i in range(len(self.chat_history) - 1, -1, -1):
            if self.chat_history[i].startswith("You:"):
                last_user_idx = i
                break
        
        # Get all agent messages after the last user message
        latest_round = []
        for i in range(last_user_idx + 1, len(self.chat_history)):
            msg = self.chat_history[i]
            if not msg.startswith("You:"):
                latest_round.append(msg)
        
        return latest_round
    
    def _draw_speech_bubbles(self, screen):
        """Draw speech bubbles above characters for the most recent round - one at a time"""
        latest_round = self._get_latest_round_messages()
        
        # Reset bubble index if round changed (new messages arrived)
        if len(latest_round) != self.last_round_size:
            self.current_bubble_index_in_round = 0
            self.last_round_size = len(latest_round)
        
        if not latest_round:
            return
        
        # Clamp bubble index to valid range
        if self.current_bubble_index_in_round >= len(latest_round):
            self.current_bubble_index_in_round = len(latest_round) - 1
        if self.current_bubble_index_in_round < 0:
            self.current_bubble_index_in_round = 0
        
        # Get the current message to display
        current_msg = latest_round[self.current_bubble_index_in_round]
        
        # Extract speaker name and message
        parts = current_msg.split(":", 1)
        if len(parts) == 2:
            speaker = parts[0].strip()
            message = parts[1].strip()
            sprite_pos = self._get_sprite_pos(speaker)
            if sprite_pos:
                # Position speech bubble above the character
                bubble_x = sprite_pos[0] + int(30 * 0.8)  # Center above sprite
                bubble_y = sprite_pos[1] - int(20 * 0.8)  # Above the sprite
                
                # Get scroll offset for this speaker
                scroll_offset = self.speech_bubble_scroll_offsets.get(speaker, 0)
                
                # Draw speech bubble with fixed height and scrollbar
                bubble_rect = self._draw_speech_bubble(
                    screen, 
                    message,
                    speaker,
                    (255, 255, 255),  # White background
                    (0, 0, 0),  # Black text
                    (bubble_x, bubble_y),
                    int(16 * 0.8),  # Smaller font size
                    self.speech_bubble_height,
                    scroll_offset,
                    speaker  # Pass speaker name for scrollbar tracking
                )
                
                # Position Next button at bottom right of the bubble
                if bubble_rect:
                    self.next_message_button.button.set_relative_position((
                        bubble_rect.right - int(130 * 0.8),  # Position at right edge
                        bubble_rect.bottom + int(10 * 0.8)  # Below the bubble
                    ))
        
        # Clean up scrollbars for speakers not currently displayed
        current_speaker = parts[0].strip() if len(parts) == 2 else None
        speakers_to_remove = []
        for speaker_key in self.speech_bubble_scrollbars:
            if speaker_key != current_speaker:
                if self.speech_bubble_scrollbars[speaker_key]:
                    self.speech_bubble_scrollbars[speaker_key].kill()
                speakers_to_remove.append(speaker_key)
        for speaker_key in speakers_to_remove:
            del self.speech_bubble_scrollbars[speaker_key]
            if speaker_key in self.speech_bubble_scroll_offsets:
                del self.speech_bubble_scroll_offsets[speaker_key]
            if speaker_key in self.speech_bubble_rects:
                del self.speech_bubble_rects[speaker_key]
    
    def _draw_speech_bubble(self, screen, text, speaker_name, bg_colour, text_colour, pos, size, max_height, scroll_offset, speaker_key=None):
        """Draw a speech bubble with text, fixed height, and pygame-gui scrollbar"""
        if speaker_key is None:
            speaker_key = speaker_name
        
        font = pygame.font.Font("resources/roboto_fonts/Roboto-Regular.ttf", size)
        name_font = pygame.font.Font("resources/roboto_fonts/Roboto-Bold.ttf", size)
        
        # Wrap text to fit within max width (increased for larger bubble)
        max_width = int(350 * 0.8)  # Wider for larger bubble
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        if not lines:
            lines = [text]
        
        # Render text lines
        text_surfaces = [font.render(line, True, text_colour) for line in lines]
        line_height = font.get_linesize()
        total_text_height = sum(surf.get_height() for surf in text_surfaces) + (len(text_surfaces) - 1) * 5
        
        # Calculate background rectangle with fixed height (larger bubble)
        max_text_width = max(surf.get_width() for surf in text_surfaces) if text_surfaces else max_width
        bg_rect = pygame.Rect(
            pos[0] - max_text_width // 2 - 10,
            pos[1] - max_height - 10,
            max_text_width + 60,  # Extra width for wider scrollbar and larger bubble
            max_height
        )
        self.speech_bubble_rects[speaker_key] = bg_rect  # Store for this speaker
        
        # Draw background (speech bubble)
        pygame.draw.rect(screen, bg_colour, bg_rect, border_radius=10)
        pygame.draw.rect(screen, text_colour, bg_rect, width=2, border_radius=10)
        
        # Draw speaker name at top
        name_surface = name_font.render(speaker_name, True, text_colour)
        name_x = bg_rect.x + (bg_rect.width - name_surface.get_width()) // 2
        screen.blit(name_surface, (name_x, bg_rect.y + 5))
        
        # Define scrollbar width first (wider for easier clicking)
        scrollbar_width = int(25 * 0.8)  # Wider scrollbar for easier clicking
        
        # Create clipping rectangle for text area
        text_area_rect = pygame.Rect(
            bg_rect.x + 10,
            bg_rect.y + name_surface.get_height() + 10,
            bg_rect.width - scrollbar_width - 15,  # Leave space for wider scrollbar
            bg_rect.height - name_surface.get_height() - 15
        )
        
        # Create or update pygame-gui scrollbar with padding
        # Add extra padding to ensure last line is fully visible
        padding = int(100 * 0.8)  # Even more padding so last line is fully visible
        scrollable_height = total_text_height + padding  # Add padding so last line is fully visible
        
        if scrollable_height > text_area_rect.height:
            scrollbar_rect = pygame.Rect(
                bg_rect.right - scrollbar_width - 8,  # More spacing from edge
                text_area_rect.y,
                scrollbar_width,
                text_area_rect.height
            )
            
            # Calculate visible percentage accounting for padding
            visible_percentage = text_area_rect.height / scrollable_height
            
            # Create scrollbar if it doesn't exist or needs repositioning for this speaker
            if speaker_key not in self.speech_bubble_scrollbars or self.speech_bubble_scrollbars[speaker_key] is None:
                self.speech_bubble_scrollbars[speaker_key] = pygame_gui.elements.UIVerticalScrollBar(
                    relative_rect=scrollbar_rect,
                    visible_percentage=visible_percentage,
                    manager=self.manager
                )
                self.speech_bubble_scrollbars[speaker_key].scroll_position = scroll_offset
            else:
                # Update scrollbar position and size
                self.speech_bubble_scrollbars[speaker_key].set_relative_position(scrollbar_rect.topleft)
                self.speech_bubble_scrollbars[speaker_key].set_dimensions((scrollbar_width, text_area_rect.height))
                self.speech_bubble_scrollbars[speaker_key].visible_percentage = visible_percentage
                # Update scroll position from scrollbar
                self.speech_bubble_scroll_offsets[speaker_key] = self.speech_bubble_scrollbars[speaker_key].scroll_position
                scroll_offset = self.speech_bubble_scroll_offsets[speaker_key]
        else:
            # Remove scrollbar if not needed for this speaker
            if speaker_key in self.speech_bubble_scrollbars and self.speech_bubble_scrollbars[speaker_key]:
                self.speech_bubble_scrollbars[speaker_key].kill()
                self.speech_bubble_scrollbars[speaker_key] = None
            scroll_offset = 0
        
        # Draw text with clipping and scrolling
        clip_rect = screen.get_clip()
        screen.set_clip(text_area_rect)
        
        # Calculate max scroll to include padding so last line is fully visible
        max_scroll = max(0, scrollable_height - text_area_rect.height)
        scroll_offset = max(0, min(scroll_offset, max_scroll))
        
        y_offset = text_area_rect.y - scroll_offset
        for text_surface in text_surfaces:
            # Show text if it's within the visible area (with generous margin)
            if y_offset + text_surface.get_height() >= text_area_rect.y - 10 and y_offset <= text_area_rect.bottom + 10:
                x_pos = text_area_rect.x + (text_area_rect.width - text_surface.get_width()) // 2
                screen.blit(text_surface, (x_pos, y_offset))
            y_offset += text_surface.get_height() + 5
        
        screen.set_clip(clip_rect)
        
        # Draw tail pointing to character
        tail_points = [
            (pos[0], bg_rect.bottom),
            (pos[0] - 10, bg_rect.bottom + 10),
            (pos[0] + 10, bg_rect.bottom + 10)
        ]
        pygame.draw.polygon(screen, bg_colour, tail_points)
        pygame.draw.polygon(screen, text_colour, tail_points, width=2)
        
        return bg_rect


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
