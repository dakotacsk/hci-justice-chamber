import pygame
import pygame_gui
import time
import math

MIN_FONT_SIZE = 18

# --- UI Components ---


class Button:
    """Wrapper for pygame-gui UIButton to maintain compatibility"""

    def __init__(self, x, y, width, height, label, manager, color=(100, 100, 200)):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.color = color
        self.button = pygame_gui.elements.UIButton(
            relative_rect=self.rect, text="", manager=manager
        )
        self._visible = True
        button_font_size = max(MIN_FONT_SIZE, int(20 * 0.8))
        self.font = pygame.font.Font(
            "resources/roboto_fonts/Roboto-Bold.ttf", button_font_size
        )
        self.label_surface = self.font.render(self.label, True, (255, 255, 255))
        self.text_padding = (16, 12)
        self._ensure_size_for_label()
        # Set custom colors
        self.button.colours["normal_bg"] = color
        self.button.colours["hovered_bg"] = tuple(min(255, c + 20) for c in color)
        self.button.colours["pressed_bg"] = tuple(max(0, c - 20) for c in color)

    def draw(self, screen):
        # pygame-gui handles drawing via UIManager; ensure sizing stays correct
        self._ensure_size_for_label()

    def _ensure_size_for_label(self):
        padding_x, padding_y = self.text_padding
        min_width = self.label_surface.get_width() + (padding_x * 2)
        min_height = self.label_surface.get_height() + (padding_y * 2)
        new_width = max(self.rect.width, min_width)
        new_height = max(self.rect.height, min_height)
        if new_width != self.rect.width or new_height != self.rect.height:
            self.rect.width = new_width
            self.rect.height = new_height
            self.button.set_dimensions((new_width, new_height))
            self.button.set_relative_position((self.rect.x, self.rect.y))

    def set_position(self, pos):
        self.rect.topleft = pos
        self.button.set_relative_position(pos)

    def draw_label(self, screen):
        if not self.is_visible():
            return
        text_rect = self.label_surface.get_rect(center=self.rect.center)
        screen.blit(self.label_surface, text_rect)

    def set_label(self, new_label):
        if new_label != self.label:
            self.label = new_label
            self.label_surface = self.font.render(self.label, True, (255, 255, 255))
            self._ensure_size_for_label()

    def hide(self):
        """Hide the underlying pygame-gui button."""
        self._visible = False
        try:
            self.button.hide()
        except Exception:
            self.button.visible = 0

    def show(self):
        """Show the underlying pygame-gui button."""
        self._visible = True
        try:
            self.button.show()
        except Exception:
            self.button.visible = 1

    def is_visible(self):
        try:
            return bool(self.button.visible)
        except Exception:
            return self._visible

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
            manager=manager,
        )
        # Track state ourselves since pygame-gui UICheckBox state can be tricky
        self._checked = is_on
        if is_on:
            try:
                self.checkbox.checked = True
            except:
                pass
        # Create label text separately
        label_font_size = max(MIN_FONT_SIZE, int(24 * 0.8))
        self.label_surface = pygame.font.Font(
            "resources/roboto_fonts/Roboto-Regular.ttf", label_font_size
        ).render(label, True, (20, 20, 20))
        self.label_pos = (self.rect.x + self.rect.width + 10, self.rect.y)

    def draw(self, screen):
        # pygame-gui handles checkbox drawing, but we draw the label
        screen.blit(self.label_surface, self.label_pos)

    @property
    def is_on(self):
        # Try multiple methods to check state
        try:
            # First try the checked attribute
            if hasattr(self.checkbox, "checked"):
                checked = self.checkbox.checked
                self._checked = bool(checked)
                return self._checked
        except:
            pass

        # Try get_state()
        try:
            state = self.checkbox.get_state()
            # UICheckBox states: when checked, might be 'selected' or contain 'selected'
            if "selected" in str(state).lower():
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

    def handle_event(self, event, button):
        # Listen for checkbox state changes
        if event.type == pygame.KEYDOWN:
            if event.key == button:
                self._checked = not self._checked
                self.checkbox.set_state(self._checked)
        if event.type == pygame_gui.UI_CHECK_BOX_CHECKED:
            if event.ui_element == self.checkbox:
                self._checked = True
        elif event.type == pygame_gui.UI_CHECK_BOX_UNCHECKED:
            if event.ui_element == self.checkbox:
                self._checked = False
        return False


class TextInputBox:
    """Multi-line text input using UITextBox with manual editing support"""

    def __init__(self, x, y, width, height, font, manager, placeholder="", voice_only=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.placeholder = placeholder
        self.font = font
        self.active = False
        self.voice_only = voice_only  # If True, disable keyboard input (voice-only mode)

        # Use UITextBox for display with scrollbars
        # Set placeholder as initial HTML if provided
        initial_html = ""
        if placeholder:
            initial_html = (
                f'<body bgcolor="#FFFFFF"><font color="#999999" pixel_size="{MIN_FONT_SIZE}">'
                f"{placeholder}</font></body>"
            )
        else:
            # Empty white background if no placeholder
            initial_html = '<body bgcolor="#FFFFFF"></body>'
        self.textbox = pygame_gui.elements.UITextBox(
            relative_rect=self.rect,
            html_text=initial_html,
            manager=manager,
            wrap_to_height=False,  # Fixed height - scrollbars will appear when content overflows
        )
        # Try to make background transparent/white by setting all possible color properties
        white = pygame.Color(255, 255, 255)
        black = pygame.Color(0, 0, 0)
        if hasattr(self.textbox, "colours"):
            # Set all background-related colors to white
            for bg_key in [
                "dark_bg",
                "normal_bg",
                "selected_bg",
                "bg",
                "background_colour",
                "misc_bg",
            ]:
                if bg_key in self.textbox.colours:
                    self.textbox.colours[bg_key] = white
            # Set text colors to black
            for text_key in ["normal_text", "text", "text_colour", "text_color"]:
                if text_key in self.textbox.colours:
                    self.textbox.colours[text_key] = black
        # Also try setting background_colour attribute directly if it exists
        if hasattr(self.textbox, "background_colour"):
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

        # Skip keyboard input if voice-only mode is enabled
        if self.voice_only and event.type == pygame.KEYDOWN:
            return  # Don't process keyboard input in voice-only mode

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
                escaped_msg = (
                    self._text.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace("\n", "<br>")
                )
                html_text = (
                    f'<body bgcolor="#FFFFFF"><font color="#000000" pixel_size="{MIN_FONT_SIZE}">'
                    f"{escaped_msg}</font></body>"
                )
            else:
                # Show placeholder if text is empty
                html_text = (
                    f'<body bgcolor="#FFFFFF"><font color="#999999" pixel_size="{MIN_FONT_SIZE}">'
                    f"{self.placeholder}</font></body>"
                    if self.placeholder
                    else '<body bgcolor="#FFFFFF"></body>'
                )
            self.textbox.html_text = html_text
            self.textbox.rebuild()
            # Ensure white background after rebuild - try all possible keys
            if hasattr(self.textbox, "colours"):
                white = pygame.Color(255, 255, 255)
                for bg_key in [
                    "dark_bg",
                    "normal_bg",
                    "selected_bg",
                    "bg",
                    "background_colour",
                    "misc_bg",
                ]:
                    if bg_key in self.textbox.colours:
                        self.textbox.colours[bg_key] = white

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        self._lines = value.split("\n") if value else [""]
        if value and value.strip():  # Only show text if it's not empty/whitespace
            escaped_msg = (
                value.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\n", "<br>")
            )
            html_text = (
                f'<body bgcolor="#FFFFFF"><font color="#000000" pixel_size="{MIN_FONT_SIZE}">'
                f"{escaped_msg}</font></body>"
            )
        else:
            # Show placeholder if text is empty
            html_text = (
                f'<body bgcolor="#FFFFFF"><font color="#999999" pixel_size="{MIN_FONT_SIZE}">'
                f"{self.placeholder}</font></body>"
                if self.placeholder
                else '<body bgcolor="#FFFFFF"></body>'
            )
        self.textbox.html_text = html_text
        self.textbox.rebuild()
        # Ensure white background after rebuild
        if hasattr(self.textbox, "colours"):
            white = pygame.Color(255, 255, 255)
            for bg_key in ["dark_bg", "normal_bg", "selected_bg", "bg"]:
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
    def __init__(self, screen_width, screen_height, speech_recognizer=None):
        self.manager = pygame_gui.UIManager((screen_width, screen_height))
        self.speech_recognizer = speech_recognizer
        self.font_title = pygame.font.Font(
            "resources/roboto_fonts/Roboto-Bold.ttf",
            max(MIN_FONT_SIZE, int(48 * 0.8)),
        )
        self.font_label = pygame.font.Font(
            "resources/roboto_fonts/Roboto-Regular.ttf",
            max(MIN_FONT_SIZE, int(32 * 0.8)),
        )
        self.font_input = pygame.font.Font(
            "resources/roboto_fonts/Roboto-Regular.ttf",
            max(MIN_FONT_SIZE, int(28 * 0.8)),
        )
        self.width = screen_width
        self.height = screen_height
        
        # Voice mode state
        self.voice_mode_active = True
        self.voice_detected_time = 0
        self.mic_rect = None
        self.active_input_index = 0  # Track which input box is currently active
        # Match ChatGUI style - use same text and color
        self.hold_text = self.font_input.render("Unmute mic to talk", True, (85, 85, 85))
        
        # Question navigation state - show one question at a time
        self.current_question_index = 0  # Which question is currently displayed (0-3)
        
        self.questions = [
            "1. What is the name or title of your justice framework?",
            "2. In 1-2 sentences, what does justice mean in this worldview?",
            "3. What are its core values or principles? (comma-separated)",
            "4. Describe your advocate's tone and personality.",
        ]

        self.input_boxes = []
        self.labels = []

        input_w = self.width * 0.6
        input_h = int(
            100 * 0.8
        )  # Increased height to show more content before scrolling
        start_y = int(150 * 0.8)
        label_to_box_spacing = int(40 * 0.8)  # Space between label and input box
        box_height = input_h
        box_to_next_label_spacing = int(
            20 * 0.8
        )  # Space after input box before next label
        y_padding = (
            label_to_box_spacing + box_height + box_to_next_label_spacing
        )  # Total spacing between labels

        # Create labels and input boxes (positions will be set dynamically in draw() for slide layout)
        for i, q in enumerate(self.questions):
            label_surface = self.font_label.render(
                q, True, (255, 255, 255)
            )  # White text for dark blue background
            # Store label surface, position will be set in draw()
            self.labels.append((label_surface, (0, 0)))  # Position set in draw()

            # Use TextInputBox for multi-line input with scrollbars
            # Initial position doesn't matter - will be repositioned in draw() for slide layout
            box_rect = pygame.Rect(0, 0, input_w, input_h)
            # Use generic placeholder - will be updated dynamically based on current question
            placeholder_text = "Hold SPACE and speak your answer..."
            textbox = TextInputBox(
                box_rect.x,
                box_rect.y,
                box_rect.width,
                box_rect.height,
                self.font_input,
                self.manager,
                placeholder=placeholder_text,
                voice_only=True,  # Enable voice-only mode for creation form
            )
            textbox.question_index = i  # Store question index for dynamic placeholder updates
            # Hide textbox initially - will be shown only for current question
            if hasattr(textbox, 'textbox'):
                textbox.textbox.hide()
            self.input_boxes.append(textbox)
        
        # Set first input box as active by default
        if self.input_boxes:
            self.input_boxes[0].active = True

        # Position "Next Question" / "Save" button below the input box
        # Button will be repositioned based on current question
        button_width = 240
        button_height = 64
        button_y = start_y + label_to_box_spacing + box_height + 30
        button_rect = pygame.Rect(
            self.width / 2 - button_width / 2,
            button_y,
            button_width,
            button_height,
        )
        self.next_button = Button(
            button_rect.x,
            button_rect.y,
            button_rect.width,
            button_rect.height,
            "Next Question (T)",
            self.manager,
        )

        back_rect = pygame.Rect(20, 20, 50, 50)
        self.back_button = Button(
            back_rect.x,
            back_rect.y,
            back_rect.width,
            back_rect.height,
            "<",
            self.manager,
        )

    def handle_event(self, event):
        self.manager.process_events(event)

        # Handle keyboard navigation - T key moves to next question
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_t:
                # Move to next question, or save if on last question
                if self.current_question_index < len(self.questions) - 1:
                    # Move to next question (slide transition)
                    self.current_question_index += 1
                    self.active_input_index = self.current_question_index
                    # Update active state
                    for i, box in enumerate(self.input_boxes):
                        box.active = (i == self.active_input_index)
                else:
                    # On last question, save if all fields are filled
                    return self._try_save()
            elif event.key == pygame.K_UP:
                # Move to previous question (slide transition)
                if self.current_question_index > 0:
                    self.current_question_index -= 1
                    self.active_input_index = self.current_question_index
                    for i, box in enumerate(self.input_boxes):
                        box.active = (i == self.active_input_index)
            elif event.key == pygame.K_DOWN:
                # Move to next question (same as T, but doesn't save on last)
                if self.current_question_index < len(self.questions) - 1:
                    self.current_question_index += 1
                    self.active_input_index = self.current_question_index
                    for i, box in enumerate(self.input_boxes):
                        box.active = (i == self.active_input_index)
            elif event.key == pygame.K_LEFT:
                # LEFT arrow key to exit (handled in main.py, but return signal here too)
                return "back"

        # Track which input box is clicked/active
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, box in enumerate(self.input_boxes):
                if box.rect.collidepoint(event.pos):
                    self.active_input_index = i
                    self.current_question_index = i  # Sync question index
                    # Update active state for all boxes
                    for j, b in enumerate(self.input_boxes):
                        b.active = (j == i)
                    break

        # Handle microphone button click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.mic_rect and self.mic_rect.collidepoint(event.pos):
                self.voice_mode_active = not self.voice_mode_active
                return "mic_toggled"

        # Skip keyboard events for voice-only input boxes (they only accept voice input)
        # Only handle mouse events for the currently visible input box (for clicking/focusing)
        if 0 <= self.current_question_index < len(self.input_boxes):
            # Only process mouse events, not keyboard events (voice-only mode)
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.input_boxes[self.current_question_index].handle_event(event)

        # Handle next/save button click
        if self.next_button.is_clicked(event):
            if self.current_question_index < len(self.questions) - 1:
                # Move to next question
                self.current_question_index += 1
                self.active_input_index = self.current_question_index
                for i, box in enumerate(self.input_boxes):
                    box.active = (i == self.active_input_index)
            else:
                # Save if on last question
                return self._try_save()
        
        if self.back_button.is_clicked(event):
            return "back"
        return None
    
    def _try_save(self):
        """Try to save if all fields are filled"""
        if all(self.input_boxes[i].text for i in range(len(self.input_boxes))):
            return {
                "name": self.input_boxes[0].text,
                "definition": self.input_boxes[1].text,
                "values": self.input_boxes[2].text,
                "tone": self.input_boxes[3].text,
            }
        return None
    
    def handle_voice_input(self, text):
        """Handle voice input by adding it to the currently active input box"""
        # Use current_question_index instead of active_input_index for voice input
        if 0 <= self.current_question_index < len(self.input_boxes):
            active_box = self.input_boxes[self.current_question_index]
            # Append voice input to existing text (add space if there's existing text)
            if active_box.text:
                active_box.text = active_box.text + " " + text
            else:
                active_box.text = text
            self.set_voice_detected()
            self.active_input_index = self.current_question_index
    
    def set_voice_detected(self):
        """Call this when voice input is detected to update the indicator"""
        import time
        self.voice_detected_time = time.time()
    
    def get_voice_detected(self):
        """Return voice_detected_time"""
        return self.voice_detected_time
    
    def is_voice_mode_active(self):
        """Check if voice mode is currently active"""
        return self.voice_mode_active
    
    def _draw_microphone_indicator(self, screen):
        """Draw a microphone icon that flashes green when loud audio is detected, red when voice mode is off"""
        # Position at bottom center of screen
        mic_size = int(50 * 0.8)
        mic_x = self.width / 2 - mic_size / 2
        mic_y = self.height - 100

        # Store rect for click detection (make it slightly larger for easier clicking)
        click_padding = int(10 * 0.8)
        self.mic_rect = pygame.Rect(
            mic_x - click_padding,
            mic_y - click_padding,
            mic_size + (click_padding * 2),
            mic_size + (click_padding * 2),
        )

        # If voice mode is inactive, show red
        if not self.voice_mode_active:
            mic_color = (200, 50, 50)  # Red when voice mode is deactivated
            text_rect = self.hold_text.get_rect()
            # Position text below microphone (matching ChatGUI positioning relative to mic)
            text_rect.top = mic_y + mic_size + 10
            text_rect.centerx = self.width / 2
            screen.blit(self.hold_text, text_rect)
        else:
            # Get current audio level from speech recognizer
            audio_level = 0.0
            if self.speech_recognizer:
                audio_level = self.speech_recognizer.get_audio_level()

            # Threshold for "loud" audio (adjust as needed, 0.05 = 5% of max volume)
            loud_threshold = 0.05

            # Color: green when loud audio detected, gray when quiet
            if (
                time.time() - self.voice_detected_time < 1
                or audio_level > loud_threshold
            ):
                # Active state - green color (brightness based on audio level)
                mic_color = (50, 250, 50)  # Green when active, brighter = louder
                if audio_level > loud_threshold:
                    self.set_voice_detected()
            else:
                # Idle state - gray color
                mic_color = (150, 150, 150)  # Gray when idle

        # Draw microphone icon (simple shape)
        # Microphone body (rectangle)
        body_width = int(mic_size * 0.4)
        body_height = int(mic_size * 0.7)
        body_x = mic_x + (mic_size - body_width) // 2
        body_y = mic_y
        pygame.draw.rect(
            screen,
            mic_color,
            (body_x, body_y, body_width, body_height),
            border_radius=3,
        )

        # Microphone stand (base)
        stand_width = int(mic_size * 0.6)
        stand_height = int(mic_size * 0.15)
        stand_x = mic_x + (mic_size - stand_width) // 2
        stand_y = mic_y + body_height
        pygame.draw.rect(
            screen,
            mic_color,
            (stand_x, stand_y, stand_width, stand_height),
            border_radius=2,
        )

        # Microphone grille lines (optional detail)
        for i in range(3):
            line_y = body_y + int(body_height * (0.3 + i * 0.2))
            pygame.draw.line(
                screen,
                mic_color,
                (body_x + 2, line_y),
                (body_x + body_width - 2, line_y),
                width=1,
            )
        
        # Progress indicator is now drawn in draw() method at the top

    def draw(self, screen):
        screen.fill((20, 20, 40))  # Dark blue background
        
        # Draw slide/page indicator at top (H1: Visibility of system status)
        self._draw_progress_indicator(screen)
        
        title_surface = self.font_title.render(
            "Create Your Justice Advocate", True, (255, 255, 255)  # White text
        )
        screen.blit(
            title_surface,
            (self.width / 2 - title_surface.get_width() / 2, int(80 * 0.8)),
        )

        # Slide-based display - only show current question (like separate pages)
        if 0 <= self.current_question_index < len(self.labels):
            label, pos = self.labels[self.current_question_index]
            # Reposition label for slide layout (centered, larger)
            label_y = int(200 * 0.8)
            screen.blit(label, (self.width / 2 - label.get_width() / 2, label_y))
        
        # Hide all textboxes first, then show only the current one
        for i, box in enumerate(self.input_boxes):
            if hasattr(box, 'textbox'):
                if i == self.current_question_index:
                    box.textbox.show()
                else:
                    box.textbox.hide()
        
        # Only draw the current question's input box (centered, larger for slide feel)
        if 0 <= self.current_question_index < len(self.input_boxes):
            current_box = self.input_boxes[self.current_question_index]
            # Reposition input box for slide layout
            input_w = int(self.width * 0.7)  # Wider for slide feel
            input_h = int(150 * 0.8)  # Taller for slide feel
            input_x = int(self.width / 2 - input_w / 2)
            input_y = int(280 * 0.8)
            
            # Update rect and textbox dimensions
            current_box.rect.width = input_w
            current_box.rect.height = input_h
            current_box.rect.x = input_x
            current_box.rect.y = input_y
            # Update the underlying UITextBox dimensions
            if hasattr(current_box, 'textbox'):
                current_box.textbox.set_dimensions((input_w, input_h))
                current_box.textbox.set_relative_position((input_x, input_y))
            
            current_box.draw(screen)
            
            # Highlight the active input box with a subtle border
            pygame.draw.rect(
                screen,
                (100, 200, 255),  # Light blue border
                current_box.rect,
                width=3,
            )
            
            # Update placeholder text dynamically based on current question
            # This ensures the placeholder always shows the correct question number
            if hasattr(current_box, 'question_index'):
                updated_placeholder = f"Hold SPACE and speak your answer for question {self.current_question_index + 1}..."
                if current_box.placeholder != updated_placeholder:
                    current_box.placeholder = updated_placeholder
                    # Update the textbox placeholder if empty
                    if not current_box.text:
                        current_box.text = ""  # This will trigger placeholder display
            
            # Show voice-only indicator if box is empty (centered, but below the placeholder area)
            if not current_box.text:
                voice_indicator = self.font_input.render(
                    "Voice input only - Hold SPACE to speak", 
                    True, 
                    (120, 120, 120)  # Slightly darker gray
                )
                indicator_rect = voice_indicator.get_rect()
                indicator_rect.centerx = current_box.rect.centerx
                # Position below center to avoid overlapping with placeholder
                indicator_rect.centery = current_box.rect.centery + 20
                screen.blit(voice_indicator, indicator_rect)

        # Update button label based on current question
        if self.current_question_index < len(self.questions) - 1:
            self.next_button.set_label("Next Question (T)")
        else:
            self.next_button.set_label("Save Advocate (T)")
        
        # Position button below input box
        button_y = int(280 * 0.8) + int(150 * 0.8) + 40
        self.next_button.set_position((self.width / 2 - self.next_button.rect.width / 2, button_y))
        
        self.next_button.draw(screen)
        
        # Back button hidden - use LEFT arrow key instead (H3: User control and freedom)
        # self.back_button.draw(screen)  # Hidden but functionality available via LEFT key
        
        # Draw microphone indicator
        self._draw_microphone_indicator(screen)
        
        # Draw navigation hints (H6: Recognition rather than recall)
        # Use LEFT instead of arrow symbol for better compatibility
        hint_text = self.font_input.render(
            "UP/DOWN: Navigate | T: Next/Save | LEFT: Back", True, (180, 180, 180)
        )
        hint_rect = hint_text.get_rect()
        hint_rect.centerx = self.width / 2
        hint_rect.bottom = self.height - 20
        screen.blit(hint_text, hint_rect)

        # Update and draw pygame-gui elements (including UITextBox with scrollbars)
        self.manager.update(pygame.time.get_ticks() / 1000.0)
        self.manager.draw_ui(screen)
        self.next_button.draw_label(screen)
        # self.back_button.draw_label(screen)  # Hidden - use LEFT key instead
    
    def _draw_progress_indicator(self, screen):
        """Draw progress indicator showing which slide/page (H1: Visibility of system status)"""
        # Draw progress dots/circles at the top
        dot_radius = 8
        dot_spacing = 30
        total_width = (len(self.questions) - 1) * dot_spacing
        start_x = self.width / 2 - total_width / 2
        y_pos = int(30 * 0.8)
        
        for i in range(len(self.questions)):
            x_pos = start_x + i * dot_spacing
            # Current question is filled, others are outlined
            if i == self.current_question_index:
                pygame.draw.circle(screen, (100, 200, 255), (int(x_pos), y_pos), dot_radius)
            else:
                pygame.draw.circle(screen, (100, 200, 255), (int(x_pos), y_pos), dot_radius, width=2)
        
        # Draw progress text
        progress_text = self.font_input.render(
            f"Page {self.current_question_index + 1} of {len(self.questions)}", 
            True, 
            (200, 200, 200)
        )
        progress_rect = progress_text.get_rect()
        progress_rect.centerx = self.width / 2
        progress_rect.top = y_pos + dot_radius + 10
        screen.blit(progress_text, progress_rect)


class ChatGUI:
    def __init__(
        self,
        agents,
        screen_width,
        screen_height,
        selected_advocate_key=None,
        num_custom_advocates=0,
        speech_recognizer=None,
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.manager = pygame_gui.UIManager((screen_width, screen_height))
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Justice Council")
        self.speech_recognizer = (
            speech_recognizer  # Store reference to speech recognizer for audio levels
        )

        # Resources
        self.background_image = pygame.image.load("resources/background.jpg").convert()
        self.background_image = pygame.transform.scale(
            self.background_image, (self.screen_width, self.screen_height)
        )
        # Removed dialogue_box_rect - using speech bubbles instead

        # Sprites - load default justices
        self.sprites = {
            "Sam (Utilitarian)": pygame.transform.scale(
                pygame.image.load("resources/sprites/utilitarian.png").convert_alpha(),
                (int(90 * 0.8), int(150 * 0.8)),
            ),
            "Amara (Restorative)": pygame.transform.scale(
                pygame.image.load("resources/sprites/restorative.png").convert_alpha(),
                (int(90 * 0.8), int(150 * 0.8)),
            ),
            "Jamie (Meritocracy)": pygame.transform.scale(
                pygame.image.load("resources/sprites/meritocracy.png").convert_alpha(),
                (int(90 * 0.8), int(150 * 0.8)),
            ),
            "Jordan (Rawlsian)": pygame.transform.scale(
                pygame.image.load("resources/sprites/rawlsian.png").convert_alpha(),
                (int(90 * 0.8), int(150 * 0.8)),
            ),
        }

        # Load mystery justice sprite for custom justices
        self.mystery_sprite = pygame.transform.scale(
            pygame.image.load("resources/sprites/mystery_justice.png").convert_alpha(),
            (int(80 * 0.8), int(120 * 0.8)),
        )

        # Track which custom justice is currently selected (only one at a time)
        self.selected_custom_justice = (
            selected_advocate_key
            if selected_advocate_key
            and selected_advocate_key
            not in [
                "Sam (Utilitarian)",
                "Amara (Restorative)",
                "Jamie (Meritocracy)",
                "Jordan (Rawlsian)",
            ]
            else None
        )

        # State & UI
        self.font = pygame.font.Font(
            "resources/roboto_fonts/Roboto-Regular.ttf",
            max(MIN_FONT_SIZE, int(24 * 0.8)),
        )
        self.agents = agents
        self.chat_history = []
        self.current_message_index = -1  # Index of current message being displayed
        self.current_bubble_index_in_round = (
            0  # Which bubble in the current round we're showing
        )
        self.last_round_size = 0  # Track when round changes to reset bubble index
        self.speech_bubble_height = max(
            int(200 * 0.8), MIN_FONT_SIZE * 10
        )  # Increased height for speech bubbles
        self.speech_bubble_scroll_offsets = (
            {}
        )  # Scroll offsets per speaker for long messages
        self.speech_bubble_rects = {}  # Store speech bubble positions per speaker
        self.speech_bubble_scrollbars = {}  # pygame-gui scrollbars per speech bubble

        # Track which agents are currently thinking (generating responses)
        self.thinking_agents = (
            set()
        )  # Set of agent names that are currently generating responses
        self.thinking_animation_time = 0  # For blinking animation

        # Voice input indicator state
        self.voice_detected_time = 0  # Timestamp when voice was last detected
        self.voice_indicator_duration = (
            1.0  # How long to show "active" state (in seconds)
        )
        self.voice_mode_active = True  # Track whether voice mode is active
        self.mic_rect = None  # Store microphone rect for click detection

        # Hold space bar for mic text
        self.hold_text = self.font.render("Unmute mic to talk", True, (85, 85, 85))

        input_box_x = int((1560 - 40 - 500) * 0.8)
        input_box_y = int(40 * 0.8)
        input_box_width = int(500 * 0.8)
        input_box_height = int(self.screen_height * 0.2)

        """self.main_input_box = TextInputBox(
            input_box_x,
            input_box_y,
            input_box_width,
            input_box_height,
            pygame.font.Font(
                "resources/roboto_fonts/Roboto-Regular.ttf",
                max(MIN_FONT_SIZE, int(24 * 0.8)),
            ),
            self.manager,
            placeholder="Your voice input will appear here (ask a question about justice)",
        )"""

        submit_rect = pygame.Rect(
            input_box_x + input_box_width - 180,
            input_box_y + input_box_height + 10,
            180,
            50,
        )
        """self.submit_button = Button(
            submit_rect.x,
            submit_rect.y,
            submit_rect.width,
            submit_rect.height,
            "Submit",
            self.manager,
        )"""

        button_margin = 20
        create_button_width = 460
        create_button_height = 60
        create_rect = pygame.Rect(
            self.screen_width - create_button_width - button_margin,
            self.screen_height - create_button_height - button_margin,
            create_button_width,
            create_button_height,
        )
        """self.create_advocate_button = Button(
            create_rect.x,
            create_rect.y,
            create_rect.width,
            create_rect.height,
            "Create custom Justice Advocate",
            self.manager,
        )"""

        # Add button to select/manage advocates
        select_button_width = create_button_width
        select_button_height = create_button_height
        select_rect = pygame.Rect(
            self.screen_width - select_button_width - button_margin,
            create_rect.y - select_button_height - 10,
            select_button_width,
            select_button_height,
        )
        """self.select_advocate_button = Button(
            select_rect.x,
            select_rect.y,
            select_rect.width,
            select_rect.height,
            "Select a custom Justice Advocate",
            self.manager,
            color=(100, 150, 200),
        )"""

        # Removed prev/next buttons - not needed with speech bubbles

        self.checkboxes = self._create_checkboxes()
        self.checkbox_label = pygame.font.Font(
            "resources/roboto_fonts/Roboto-Regular.ttf",
            max(MIN_FONT_SIZE, int(24 * 0.8)),
        ).render(
            "Select the character(s) you would like to talk to:",
            True,
            (20, 20, 20),  # Black text for visibility
        )
        self.checkboxes[0]._checked = True
        self.checkboxes[0].checkbox.set_state(True)

        # Next button will be positioned dynamically next to speech bubble
        # Create it initially, position will be updated when bubble is drawn
        # Make it wider to accommodate counter text like "Next Response (1/5)"
        next_button_rect = pygame.Rect(0, 0, 240, 50)
        self.next_message_button = Button(
            next_button_rect.x,
            next_button_rect.y,
            next_button_rect.width,
            next_button_rect.height,
            "Next Response",
            self.manager,
        )
        # Keep next button hidden until multiple responses exist
        self.next_message_button.hide()

        self.current_caption = ""
        self.caption_duration = 2000  # ms to display
        self.caption_timestamp = 0
        self.current_speaker = ""

    def _create_checkboxes(self):
        checkboxes = []
        x, y = int(60 * 0.8), int(100 * 0.8)
        for agent in self.agents.values():
            checkbox_rect = pygame.Rect(x, y, int(20 * 0.8), int(20 * 0.8))
            checkbox = CheckBox(
                checkbox_rect.x,
                checkbox_rect.y,
                checkbox_rect.width,
                checkbox_rect.height,
                agent.profile.name,
                self.manager,
            )
            checkboxes.append(checkbox)
            y += int(40 * 0.8)
        return checkboxes

    def handle_event(self, event):
        self.manager.process_events(event)
        # Map checkboxes to buttons: LEFT, UP, RIGHT, DOWN only (T reserved for creation mode)
        # SPACE is reserved exclusively for microphone muting - never used for checkboxes
        button = [pygame.K_LEFT, pygame.K_UP, pygame.K_RIGHT, pygame.K_DOWN]
        # Only map buttons to checkboxes that exist (max 4 buttons for 4 default agents)
        for i, checkbox in enumerate(self.checkboxes):
            if i < len(button):  # Only map if we have a button available
                checkbox.handle_event(event, button[i])
        
        # Handle 'C' key to toggle custom advocate (if one is selected)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c:
                # Find the custom advocate checkbox (if it exists)
                for checkbox in self.checkboxes:
                    if (self.selected_custom_justice and 
                        checkbox.label == self.selected_custom_justice):
                        # Toggle the custom advocate checkbox
                        checkbox._checked = not checkbox._checked
                        checkbox.checkbox.set_state(checkbox._checked)
                        break

        # Handle next button for cycling through messages
        """if self.next_message_button.is_clicked(event):
            self._next_message()"""

        # Handle select advocate button
        """if self.select_advocate_button.is_clicked(event):
            return "select_advocate"
        """

        # Handle microphone button click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.mic_rect and self.mic_rect.collidepoint(event.pos):
                self.voice_mode_active = not self.voice_mode_active
                return "mic_toggled"

        # Handle scroll wheel for speech bubble scrolling
        if event.type == pygame.MOUSEWHEEL:
            # Check which bubble the mouse is over and scroll that one
            mouse_pos = pygame.mouse.get_pos()
            latest_round = self._get_latest_round_messages()
            for msg in latest_round:
                parts = msg.split(":", 1)
                if len(parts) == 2:
                    speaker = parts[0].strip()
                    if (
                        speaker in self.speech_bubble_scrollbars
                        and self.speech_bubble_scrollbars[speaker]
                    ):
                        bubble_rect = self.speech_bubble_rects.get(speaker)
                        if bubble_rect and bubble_rect.collidepoint(mouse_pos):
                            # Update scrollbar position via pygame-gui
                            current_scroll = self.speech_bubble_scrollbars[
                                speaker
                            ].scroll_position
                            new_scroll = max(
                                0,
                                min(
                                    current_scroll - event.y * 20,
                                    self.speech_bubble_scrollbars[speaker].bottom_limit,
                                ),
                            )
                            self.speech_bubble_scrollbars[speaker].scroll_position = (
                                new_scroll
                            )
                            self.speech_bubble_scroll_offsets[speaker] = new_scroll
                            break

    def set_caption(self, text):
        self.current_caption = text
        self.caption_timestamp = pygame.time.get_ticks()

    def draw_caption(self, screen):
        # Hide caption after duration
        if pygame.time.get_ticks() - self.caption_timestamp > self.caption_duration:
            return

        if not self.current_caption:
            return

        font = pygame.font.SysFont("Arial", 18, bold=True)

        # ---------- WORD WRAP ----------
        max_width = screen.get_width() - 80  # 40px padding each side
        words = self.current_caption.split(" ")
        lines = []
        current_line = ""

        for word in words:
            # Test width if we add the new word
            test_line = current_line + word + " "
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                # Current line full → push to list
                lines.append(current_line.strip())
                current_line = word + " "

        # Add last line
        if current_line:
            lines.append(current_line.strip())
        # --------------------------------

        # Render each line
        rendered_lines = [font.render(line, True, (255, 255, 255)) for line in lines]

        # Calculate total height
        line_height = rendered_lines[0].get_height()
        total_height = len(rendered_lines) * line_height + (len(rendered_lines) - 1) * 4

        # Position bottom centered
        center_x = screen.get_width() // 2
        base_y = screen.get_height() - 60

        # Compute background rect
        max_line_width = max(surface.get_width() for surface in rendered_lines)
        padding = 12

        bg_rect = pygame.Rect(
            center_x - max_line_width // 2 - padding,
            base_y - total_height - padding,
            max_line_width + padding * 2,
            total_height + padding * 2,
        )

        # Background (transparent black)
        caption_bg = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        caption_bg.fill((0, 0, 0, 150))

        # Draw background
        screen.blit(caption_bg, (bg_rect.x, bg_rect.y))

        # Draw wrapped lines
        y_offset = bg_rect.y + padding
        for surf in rendered_lines:
            x = center_x - surf.get_width() // 2
            screen.blit(surf, (x, y_offset))
            y_offset += line_height + 4  # small spacing

    def _get_current_message(self):
        """Get the current message being displayed"""
        if self.chat_history and 0 <= self.current_message_index < len(
            self.chat_history
        ):
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
                if (
                    current_speaker in self.speech_bubble_scrollbars
                    and self.speech_bubble_scrollbars[current_speaker]
                ):
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

        # Update thinking animation time
        import time

        self.thinking_animation_time = time.time()

        # Initialize current message index if needed
        if self.current_message_index < 0 and self.chat_history:
            # Find first agent message
            for i, msg in enumerate(self.chat_history):
                if not msg.startswith("You:"):
                    self.current_message_index = i
                    break

        # self.main_input_box.draw(screen)
        # self.create_advocate_button.draw(screen)
        # self.select_advocate_button.draw(screen)

        # Draw microphone indicator
        self._draw_microphone_indicator(screen)

        """latest_round = self._get_latest_round_messages()
        if len(latest_round) <= 1:
            self.next_message_button.hide()"""

        screen.blit(self.checkbox_label, (int(60 * 0.8), int(60 * 0.8)))
        for checkbox in self.checkboxes:
            checkbox.draw(screen)

        self._draw_sprites(screen)

        # Draw speech bubbles above characters (scrollbar updates handled within _draw_speech_bubble)
        # self._draw_speech_bubbles(screen)

        # Draw caption
        self.draw_caption(screen)

        self.manager.update(pygame.time.get_ticks() / 1000.0)
        self.manager.draw_ui(screen)
        # self.create_advocate_button.draw_label(screen)
        # self.select_advocate_button.draw_label(screen)
        """if len(latest_round) > 1 and self.next_message_button.is_visible():
            self.next_message_button.draw_label(screen)"""

    def _get_sprite_pos(self, agent_name):
        # Position justices in a pentagon formation around the table
        # Table center is at screen center - no scaling applied to center
        import math

        # Use actual screen center, not scaled
        center_x = self.screen_width // 2  # Screen center X (624 for 1248px screen)
        center_y = self.screen_height // 2  # Screen center Y (351 for 702px screen)
        radius = int(200 * 0.8)  # Smaller radius to bring them closer together

        # Calculate pentagon positions (5 vertices evenly spaced around a circle)
        # Start at top and go clockwise
        # Angle offset: -90 degrees to start at top, then add 72 degrees per vertex (360/5 = 72)
        positions = []
        for i in range(5):
            angle = math.radians(-90 + i * 72)  # Start at top, go clockwise
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle) - 35
            positions.append([int(x), int(y)])

        # Assign positions to justices
        # Order: Top, Top-right, Bottom-right, Bottom-left, Top-left
        sprite_positions = {
            "Jamie (Meritocracy)": positions[4],  # Top
            "Jordan (Rawlsian)": positions[1],  # Top-right
            "Amara (Restorative)": positions[2],  # Bottom-right
            "Sam (Utilitarian)": positions[3],  # Bottom-left
        }

        sprite_positions["Sam (Utilitarian)"][0] = sprite_positions[
            "Sam (Utilitarian)"
        ][0] - int(70 * 0.8)
        sprite_positions["Jamie (Meritocracy)"][0] = sprite_positions[
            "Sam (Utilitarian)"
        ][0] - int(70 * 0.8)

        # Custom justice gets the 5th position (top-left)
        # If not in default positions, it's a custom advocate
        if agent_name not in sprite_positions:
            return positions[0]  # Top-left position

        return sprite_positions.get(agent_name)

    def _draw_sprites(self, screen):
        # Simple logic: checkbox checked = sprite appears
        for checkbox in self.checkboxes:
            if checkbox.is_on:
                sprite_pos = self._get_sprite_pos(checkbox.label)
                if sprite_pos:
                    # Use default sprite if available, otherwise use mystery sprite for custom advocates
                    sprite_surface = self.sprites.get(checkbox.label, self.mystery_sprite)
                    screen.blit(sprite_surface, sprite_pos)

                    """# Draw blinking border if agent is thinking
                    if checkbox.label in self.thinking_agents:
                        self._draw_thinking_border(screen, sprite_pos, sprite_surface)"""

                    # Draw "!" bubble if agent has a ready response that's not currently displayed
                    if self.current_speaker == checkbox.label:
                        self._draw_exclamation_bubble(screen, sprite_pos)

    def _draw_thinking_border(self, screen, sprite_pos, sprite_surface):
        """Draw a blinking border around a sprite to indicate thinking"""
        # Calculate border rectangle around sprite
        border_padding = int(5 * 0.8)
        border_rect = pygame.Rect(
            sprite_pos[0] - border_padding,
            sprite_pos[1] - border_padding,
            sprite_surface.get_width() + (border_padding * 2),
            sprite_surface.get_height() + (border_padding * 2),
        )

        # Blinking effect: oscillate between visible and semi-transparent
        # Use sine wave for smooth blinking (blinks every ~1 second)
        blink_speed = 3.0  # Speed of blinking
        current_time = time.time()
        alpha = int(128 + 127 * math.sin(current_time * blink_speed))

        # Create a surface for the border with alpha
        border_surface = pygame.Surface(
            (border_rect.width, border_rect.height), pygame.SRCALPHA
        )

        # Draw border (outline only, not filled)
        border_color = (100, 200, 255, alpha)  # Light blue with alpha
        border_width = int(3 * 0.8)

        # Draw border rectangle
        pygame.draw.rect(
            border_surface,
            border_color,
            (0, 0, border_rect.width, border_rect.height),
            width=border_width,
            border_radius=int(5 * 0.8),
        )

        # Blit the border surface onto the screen
        screen.blit(border_surface, border_rect.topleft)

    def _agent_has_ready_response(self, agent_name):
        """Check if an agent has a response ready but not currently displayed"""
        latest_round = self._get_latest_round_messages()
        if not latest_round:
            return False

        # Check if this agent has a message in the latest round
        for msg in latest_round:
            parts = msg.split(":", 1)
            if len(parts) == 2:
                speaker = parts[0].strip()
                if speaker == agent_name:
                    # Check if this is the currently displayed message
                    if self.current_bubble_index_in_round < len(latest_round):
                        current_msg = latest_round[self.current_bubble_index_in_round]
                        if current_msg == msg:
                            # This is the currently displayed message, don't show "!"
                            return False
                    # Agent has a ready response that's not currently displayed
                    return True

        return False

    def _draw_exclamation_bubble(self, screen, sprite_pos):
        """Draw a small speech bubble with '!' above a sprite - positioned where the actual speech bubble will appear"""
        # Position bubble at the same location as the actual speech bubble will be
        # This ensures the actual speech bubble will cover it when displayed
        bubble_size = int(40 * 0.8)
        bubble_x = sprite_pos[0] + int(
            30 * 0.8
        )  # Center above sprite (same as speech bubble)
        tail_bottom_y = sprite_pos[1] - int(
            20 * 0.8
        )  # Where tail points to (same as speech bubble)

        # Position bubble so the tail comes from the bottom, with "!" clearly above it
        bubble_rect = pygame.Rect(
            bubble_x - bubble_size // 2,
            tail_bottom_y
            - bubble_size
            - int(8 * 0.8),  # Position bubble above tail point
            bubble_size,
            bubble_size,
        )

        # Draw bubble background (white)
        pygame.draw.ellipse(screen, (255, 255, 255), bubble_rect)
        pygame.draw.ellipse(screen, (0, 0, 0), bubble_rect, width=2)

        # Draw "!" text centered in the middle of the bubble
        exclamation_font = pygame.font.Font(
            "resources/roboto_fonts/Roboto-Bold.ttf",
            max(MIN_FONT_SIZE, int(24 * 0.8)),
        )
        exclamation_surface = exclamation_font.render("!", True, (0, 0, 0))
        exclamation_x = bubble_rect.centerx - exclamation_surface.get_width() // 2
        # Position "!" in the center of the bubble
        exclamation_y = bubble_rect.centery - exclamation_surface.get_height() // 2
        screen.blit(exclamation_surface, (exclamation_x, exclamation_y))

        # Draw small tail pointing down from bottom of bubble to character
        tail_points = [
            (bubble_rect.centerx, bubble_rect.bottom),  # Top of tail (bottom of bubble)
            (sprite_pos[0] + int(30 * 0.8) - 5, tail_bottom_y),  # Bottom left of tail
            (sprite_pos[0] + int(30 * 0.8) + 5, tail_bottom_y),  # Bottom right of tail
        ]
        pygame.draw.polygon(screen, (255, 255, 255), tail_points)
        pygame.draw.polygon(screen, (0, 0, 0), tail_points, width=2)

    def set_agent_thinking(self, agent_name, is_thinking):
        """Mark an agent as thinking or not thinking"""
        if is_thinking:
            self.thinking_agents.add(agent_name)
        else:
            self.thinking_agents.discard(agent_name)

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
        # Hide next button by default; it will be shown only when needed
        self.next_message_button.hide()

        latest_round = self._get_latest_round_messages()

        # Reset bubble index if round changed (new messages arrived)
        if len(latest_round) != self.last_round_size:
            self.current_bubble_index_in_round = 0
            self.last_round_size = len(latest_round)

        if not latest_round:
            self.next_message_button.hide()
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
                    max(MIN_FONT_SIZE, int(16 * 0.8)),  # Enforce minimum font size
                    self.speech_bubble_height,
                    scroll_offset,
                    speaker,  # Pass speaker name for scrollbar tracking
                )

                # Position Next button at bottom right of the bubble (only if multiple bubbles)
                latest_round = self._get_latest_round_messages()
                if bubble_rect and len(latest_round) > 1:
                    # Update button text with current position
                    current_position = self.current_bubble_index_in_round + 1
                    total_responses = len(latest_round)
                    button_text = (
                        f"Next Response ({current_position}/{total_responses})"
                    )
                    self.next_message_button.set_label(button_text)

                    self.next_message_button.show()
                    self.next_message_button.set_position(
                        (
                            bubble_rect.right - self.next_message_button.rect.width,
                            bubble_rect.bottom + 10,  # Below the bubble
                        )
                    )
                elif len(latest_round) <= 1:
                    # Hide button if only one message
                    self.next_message_button.hide()

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

    def _draw_speech_bubble(
        self,
        screen,
        text,
        speaker_name,
        bg_colour,
        text_colour,
        pos,
        size,
        max_height,
        scroll_offset,
        speaker_key=None,
    ):
        """Draw a speech bubble with text, fixed height, and pygame-gui scrollbar"""
        size = max(size, MIN_FONT_SIZE)
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
        total_text_height = (
            sum(surf.get_height() for surf in text_surfaces)
            + (len(text_surfaces) - 1) * 5
        )

        # Calculate background rectangle with fixed height (larger bubble)
        max_text_width = (
            max(surf.get_width() for surf in text_surfaces)
            if text_surfaces
            else max_width
        )
        bg_rect = pygame.Rect(
            pos[0] - max_text_width // 2 - 10,
            pos[1] - max_height - 10,
            max_text_width + 60,  # Extra width for wider scrollbar and larger bubble
            max_height,
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
            bg_rect.height - name_surface.get_height() - 15,
        )

        # Create or update pygame-gui scrollbar with padding
        # Add extra padding to ensure last line is fully visible
        padding = int(100 * 0.8)  # Even more padding so last line is fully visible
        scrollable_height = (
            total_text_height + padding
        )  # Add padding so last line is fully visible

        if scrollable_height > text_area_rect.height:
            scrollbar_rect = pygame.Rect(
                bg_rect.right - scrollbar_width - 8,  # More spacing from edge
                text_area_rect.y,
                scrollbar_width,
                text_area_rect.height,
            )

            # Calculate visible percentage accounting for padding
            visible_percentage = text_area_rect.height / scrollable_height

            # Create scrollbar if it doesn't exist or needs repositioning for this speaker
            if (
                speaker_key not in self.speech_bubble_scrollbars
                or self.speech_bubble_scrollbars[speaker_key] is None
            ):
                self.speech_bubble_scrollbars[speaker_key] = (
                    pygame_gui.elements.UIVerticalScrollBar(
                        relative_rect=scrollbar_rect,
                        visible_percentage=visible_percentage,
                        manager=self.manager,
                    )
                )
                self.speech_bubble_scrollbars[speaker_key].scroll_position = (
                    scroll_offset
                )
            else:
                # Update scrollbar position and size
                self.speech_bubble_scrollbars[speaker_key].set_relative_position(
                    scrollbar_rect.topleft
                )
                self.speech_bubble_scrollbars[speaker_key].set_dimensions(
                    (scrollbar_width, text_area_rect.height)
                )
                self.speech_bubble_scrollbars[speaker_key].visible_percentage = (
                    visible_percentage
                )
                # Update scroll position from scrollbar
                self.speech_bubble_scroll_offsets[speaker_key] = (
                    self.speech_bubble_scrollbars[speaker_key].scroll_position
                )
                scroll_offset = self.speech_bubble_scroll_offsets[speaker_key]
        else:
            # Remove scrollbar if not needed for this speaker
            if (
                speaker_key in self.speech_bubble_scrollbars
                and self.speech_bubble_scrollbars[speaker_key]
            ):
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
            if (
                y_offset + text_surface.get_height() >= text_area_rect.y - 10
                and y_offset <= text_area_rect.bottom + 10
            ):
                x_pos = (
                    text_area_rect.x
                    + (text_area_rect.width - text_surface.get_width()) // 2
                )
                screen.blit(text_surface, (x_pos, y_offset))
            y_offset += text_surface.get_height() + 5

        screen.set_clip(clip_rect)

        # Draw tail pointing to character
        tail_points = [
            (pos[0], bg_rect.bottom),
            (pos[0] - 10, bg_rect.bottom + 10),
            (pos[0] + 10, bg_rect.bottom + 10),
        ]
        pygame.draw.polygon(screen, bg_colour, tail_points)
        pygame.draw.polygon(screen, text_colour, tail_points, width=2)

        return bg_rect

    def _draw_microphone_indicator(self, screen):
        """Draw a microphone icon below the textbox that flashes green when loud audio is detected, red when voice mode is off"""
        # Position below the textbox, centered
        mic_size = int(50 * 0.8)
        mic_x = self.screen_width / 2 - mic_size / 2
        mic_y = self.screen_height - 130 - 60

        # Store rect for click detection (make it slightly larger for easier clicking)
        click_padding = int(10 * 0.8)
        self.mic_rect = pygame.Rect(
            mic_x - click_padding,
            mic_y - click_padding,
            mic_size + (click_padding * 2),
            mic_size + (click_padding * 2),
        )

        # If voice mode is inactive, show red
        if not self.voice_mode_active:
            mic_color = (200, 50, 50)  # Red when voice mode is deactivated
            text_rect = self.hold_text.get_rect()
            text_rect.top = self.screen_height - 87 - 60
            text_rect.centerx = self.screen_width / 2
            if self.current_speaker == "":
                self.screen.blit(self.hold_text, text_rect)
        else:
            # Get current audio level from speech recognizer
            audio_level = 0.0
            if self.speech_recognizer:
                audio_level = self.speech_recognizer.get_audio_level()

            # Threshold for "loud" audio (adjust as needed, 0.05 = 5% of max volume)
            loud_threshold = 0.05

            # Color: green when loud audio detected, gray when quiet
            if (
                time.time() - self.voice_detected_time < 1
                or audio_level > loud_threshold
            ):
                # Active state - green color (brightness based on audio level)
                # Scale green intensity based on audio level
                mic_color = (50, 250, 50)  # Green when active, brighter = louder
                if audio_level > loud_threshold:
                    self.set_voice_detected()
            else:
                # Idle state - gray color
                mic_color = (150, 150, 150)  # Gray when idle

        # Draw microphone icon (simple shape)
        # Microphone body (rectangle)
        body_width = int(mic_size * 0.4)
        body_height = int(mic_size * 0.7)
        body_x = mic_x + (mic_size - body_width) // 2
        body_y = mic_y
        pygame.draw.rect(
            screen,
            mic_color,
            (body_x, body_y, body_width, body_height),
            border_radius=3,
        )

        # Microphone stand (base)
        stand_width = int(mic_size * 0.6)
        stand_height = int(mic_size * 0.15)
        stand_x = mic_x + (mic_size - stand_width) // 2
        stand_y = mic_y + body_height
        pygame.draw.rect(
            screen,
            mic_color,
            (stand_x, stand_y, stand_width, stand_height),
            border_radius=2,
        )

        # Microphone grille lines (optional detail)
        for i in range(3):
            line_y = body_y + int(body_height * (0.3 + i * 0.2))
            pygame.draw.line(
                screen,
                mic_color,
                (body_x + 2, line_y),
                (body_x + body_width - 2, line_y),
                width=1,
            )

    def set_voice_detected(self):
        """Call this when voice input is detected to update the indicator"""
        import time

        self.voice_detected_time = time.time()

    def get_voice_detected(self):
        """Return voice_detected_time"""
        return self.voice_detected_time

    def is_voice_mode_active(self):
        """Check if voice mode is currently active"""
        return self.voice_mode_active


class AdvocateSelectionScreen:
    def __init__(
        self, screen_width, screen_height, custom_advocates, default_agents=None
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.manager = pygame_gui.UIManager((screen_width, screen_height))
        self.custom_advocates = custom_advocates
        self.default_agents = (
            default_agents or {}
        )  # Keep for reference but don't display

        self.font_title = pygame.font.Font(
            "resources/roboto_fonts/Roboto-Bold.ttf",
            max(MIN_FONT_SIZE, int(48 * 0.8)),
        )
        self.font_label = pygame.font.Font(
            "resources/roboto_fonts/Roboto-Regular.ttf",
            max(MIN_FONT_SIZE, int(32 * 0.8)),
        )
        self.font_small = pygame.font.Font(
            "resources/roboto_fonts/Roboto-Regular.ttf",
            max(MIN_FONT_SIZE, int(24 * 0.8)),
        )

        # Scrollable area
        self.scroll_offset = 0
        self.scroll_speed = 50
        self.item_height = 80
        self.visible_items = int((screen_height - 200) / self.item_height)
        
        # Keyboard navigation state
        self.selected_index = 0  # Which advocate is currently selected (for keyboard navigation)

        # Create buttons ONLY for custom advocates (not default justices)
        self.advocate_buttons = []
        self.delete_buttons = []  # Only for custom advocates
        self.start_y = 150
        button_height = 60
        button_width = 450
        delete_button_width = 120
        y_padding = 80

        # Add ONLY custom advocates (no default justices)
        for i, advocate in enumerate(custom_advocates):
            y_pos = self.start_y + i * y_padding
            button_rect = pygame.Rect(
                self.screen_width / 2 - button_width / 2,
                y_pos,
                button_width,
                button_height,
            )
            button = Button(
                button_rect.x,
                button_rect.y,
                button_rect.width,
                button_rect.height,
                advocate.name,
                self.manager,
                color=(100, 150, 200),
            )
            button.advocate_name = advocate.name
            button.is_custom = True
            self.advocate_buttons.append(button)

            # Add delete button for custom advocates
            delete_rect = pygame.Rect(
                button_rect.right + int(10 * 0.8),
                y_pos,
                delete_button_width,
                button_height,
            )
            delete_button = Button(
                delete_rect.x,
                delete_rect.y,
                delete_rect.width,
                delete_rect.height,
                "Delete",
                self.manager,
                color=(200, 50, 50),
            )
            delete_button.advocate_name = advocate.name
            self.delete_buttons.append(delete_button)

        # Back button - match create advocate page style
        back_rect = pygame.Rect(20, 20, 50, 50)
        self.back_button = Button(
            back_rect.x,
            back_rect.y,
            back_rect.width,
            back_rect.height,
            "<",
            self.manager,
        )

    def handle_event(self, event):
        self.manager.process_events(event)

        # Handle keyboard navigation using existing buttons (UP/DOWN/T)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                # Move selection up
                if self.selected_index > 0:
                    self.selected_index -= 1
                    # Auto-scroll if needed
                    self._update_scroll_for_selection()
                return None  # Consume event to prevent other handlers
            elif event.key == pygame.K_DOWN:
                # Move selection down
                if self.selected_index < len(self.advocate_buttons) - 1:
                    self.selected_index += 1
                    # Auto-scroll if needed
                    self._update_scroll_for_selection()
                return None  # Consume event to prevent other handlers
            elif event.key == pygame.K_t:
                # Select current advocate (only if we have buttons)
                if self.advocate_buttons and 0 <= self.selected_index < len(self.advocate_buttons):
                    return self.advocate_buttons[self.selected_index].advocate_name
                return None  # Consume event to prevent triggering creation mode
            elif event.key == pygame.K_LEFT:
                # LEFT arrow key to exit (handled in main.py, but return signal here too)
                return "back"

        # Handle scrolling
        if event.type == pygame.MOUSEWHEEL:
            max_scroll = max(
                0,
                len(self.advocate_buttons) * self.item_height
                - (self.screen_height - int(200 * 0.8)),
            )
            self.scroll_offset = max(
                0, min(self.scroll_offset - event.y * self.scroll_speed, max_scroll)
            )
            # Update button positions based on scroll
            self._update_button_positions()

        if self.back_button.is_clicked(event):
            return "back"

        # Check delete buttons first (mouse only - no button pad support to minimize buttons)
        for delete_button in self.delete_buttons:
            if delete_button.is_clicked(event):
                return ("delete", delete_button.advocate_name)

        # Check selection buttons (mouse click)
        for i, button in enumerate(self.advocate_buttons):
            if button.is_clicked(event):
                self.selected_index = i  # Update selection
                return button.advocate_name

        return None
    
    def _update_scroll_for_selection(self):
        """Auto-scroll to keep selected item visible"""
        if not self.advocate_buttons:
            return
        
        # Calculate where the selected item should be
        selected_y = self.start_y + self.selected_index * 80
        
        # Check if selected item is above visible area
        visible_top = 120
        if selected_y - self.scroll_offset < visible_top:
            self.scroll_offset = max(0, selected_y - visible_top)
            self._update_button_positions()
        
        # Check if selected item is below visible area
        visible_bottom = self.screen_height - 120
        item_bottom = selected_y + 60 - self.scroll_offset
        if item_bottom > visible_bottom:
            self.scroll_offset = max(0, selected_y + 60 - visible_bottom)
            self._update_button_positions()

    def _update_button_positions(self):
        """Update button positions based on scroll offset."""
        y_padding = 80

        for i, button in enumerate(self.advocate_buttons):
            y_pos = self.start_y + i * y_padding - self.scroll_offset
            button.set_position((button.rect.x, y_pos))

        # Update delete button positions
        for i, delete_button in enumerate(self.delete_buttons):
            y_pos = self.start_y + i * y_padding - self.scroll_offset
            delete_button.set_position((delete_button.rect.x, y_pos))

    def draw(self, screen):
        # Match create advocate page aesthetic - dark blue background
        screen.fill((20, 20, 40))  # Dark blue background

        title_surface = self.font_title.render(
            "Select a Custom Justice", True, (255, 255, 255)  # White text
        )
        screen.blit(
            title_surface,
            (self.screen_width / 2 - title_surface.get_width() / 2, int(50 * 0.8)),
        )

        # Show message if no custom advocates
        if not self.custom_advocates:
            no_advocates_label = self.font_label.render(
                "No custom justices created yet.", True, (255, 255, 255)
            )
            screen.blit(
                no_advocates_label,
                (
                    self.screen_width / 2 - no_advocates_label.get_width() / 2,
                    self.start_y,
                ),
            )

        # Draw scrollable area
        clip_rect = pygame.Rect(0, 120, self.screen_width, self.screen_height - 120)
        screen.set_clip(clip_rect)

        for i, button in enumerate(self.advocate_buttons):
            if (
                button.rect.bottom >= clip_rect.top
                and button.rect.top <= clip_rect.bottom
            ):
                button.draw(screen)
                # Highlight selected advocate for keyboard navigation
                if i == self.selected_index:
                    # Draw highlight border around selected button
                    highlight_rect = pygame.Rect(
                        button.rect.x - 3,
                        button.rect.y - 3,
                        button.rect.width + 6,
                        button.rect.height + 6,
                    )
                    pygame.draw.rect(
                        screen,
                        (100, 200, 255),  # Light blue highlight
                        highlight_rect,
                        width=3,
                        border_radius=5,
                    )

        for delete_button in self.delete_buttons:
            if (
                delete_button.rect.bottom >= clip_rect.top
                and delete_button.rect.top <= clip_rect.bottom
            ):
                delete_button.draw(screen)

        screen.set_clip(None)

        self.back_button.draw(screen)
        
        # Make back button label visible (H3: User control and freedom)
        back_label = self.font_small.render("Back (←)", True, (255, 255, 255))
        back_label_rect = back_label.get_rect()
        back_label_rect.topleft = (self.back_button.rect.right + 10, self.back_button.rect.y + 10)
        screen.blit(back_label, back_label_rect)
        
        # Show keyboard navigation hint (H6: Recognition rather than recall)
        if self.advocate_buttons:
            hint_text = self.font_small.render(
                "UP/DOWN: Navigate | T: Select | ←: Back", True, (200, 200, 200)
            )
            hint_rect = hint_text.get_rect()
            hint_rect.centerx = self.screen_width / 2
            hint_rect.bottom = self.screen_height - 20
            screen.blit(hint_text, hint_rect)

        self.manager.update(pygame.time.get_ticks() / 1000.0)
        self.manager.draw_ui(screen)
        screen.set_clip(clip_rect)
        for button in self.advocate_buttons:
            if (
                button.rect.bottom >= clip_rect.top
                and button.rect.top <= clip_rect.bottom
            ):
                button.draw_label(screen)

        for delete_button in self.delete_buttons:
            if (
                delete_button.rect.bottom >= clip_rect.top
                and delete_button.rect.top <= clip_rect.bottom
            ):
                delete_button.draw_label(screen)
        screen.set_clip(None)
        self.back_button.draw_label(screen)
