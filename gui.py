import pygame
import time

# --- UI Components ---


class Button:
    def __init__(self, x, y, width, height, label, color=(100, 100, 200)):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.color = color
        self.font = pygame.font.Font("resources/roboto_fonts/Roboto-Bold.ttf", int(24 * 0.8))

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


class CheckBox:
    def __init__(self, x, y, width, height, label, is_on=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.is_on = is_on
        self.font = pygame.font.Font("resources/roboto_fonts/Roboto-Regular.ttf", int(24 * 0.8))

    def draw(self, screen):
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 2)
        if self.is_on:
            pygame.draw.rect(screen, (0, 0, 0), (self.rect.x + 3, self.rect.y + 3, self.rect.width - 6, self.rect.height - 6))
        label_surface = self.font.render(self.label, True, (0, 0, 0))
        screen.blit(label_surface, (self.rect.x + self.rect.width + 10, self.rect.y))

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
        self.scrollbar_width = int(15 * 0.8)
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

    def clear(self):
        self.text = ""
        self.lines = [""]

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
            label_surface = self.font_label.render(q, True, (255, 255, 255))
            self.labels.append((label_surface, (self.width / 2 - input_w / 2, y_pos)))
            box = TextInputBox(
                self.width / 2 - input_w / 2,
                y_pos + int(40 * 0.8),
                input_w,
                input_h,
                self.font_input,
            )
            self.input_boxes.append(box)

        self.save_button = Button(
            self.width / 2 - int(100 * 0.8),
            start_y + len(self.questions) * y_padding,
            int(200 * 0.8),
            int(50 * 0.8),
            "Save Advocate",
        )
        self.back_button = Button(
            int(20 * 0.8),
            int(20 * 0.8),
            int(40 * 0.8),
            int(40 * 0.8),
            "<",
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
        if self.back_button.is_clicked(event):
            return "back"
        return None

    def draw(self, screen):
        screen.fill((20, 20, 40))  # Dark blue background
        title_surface = self.font_title.render(
            "Create Your Justice Advocate", True, (255, 255, 255)
        )
        screen.blit(title_surface, (self.width / 2 - title_surface.get_width() / 2, int(50 * 0.8)))

        for label, pos in self.labels:
            screen.blit(label, pos)
        for box in self.input_boxes:
            box.draw(screen)

        self.save_button.draw(screen)
        self.back_button.draw(screen)



class AdvocateSelectionScreen:
    def __init__(self, screen_width, screen_height, custom_advocates: list): # custom_advocates will be a list of AgentProfile objects
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font_title = pygame.font.Font("resources/roboto_fonts/Roboto-Bold.ttf", int(48 * 0.8))
        self.font_advocate = pygame.font.Font("resources/roboto_fonts/Roboto-Regular.ttf", int(28 * 0.8))

        self.custom_advocates = custom_advocates # Store the list of custom advocates

        self.advocate_images = {}
        # Load images for default advocates (if any) and custom advocates
        # For custom advocates, we'll need a default image or assume they have one.
        # For now, let's assume custom advocates don't have specific images and use a placeholder or default.
        # Or, if the custom advocate name matches one of the existing sprite keys, use that.
        
        # Default sprites (if needed, otherwise remove)
        default_sprites = {
            "meritocracy": "Jamie Reyes",
            "rawlsian": "Jordan Chex",
            "restorative": "Amara Ndlovu",
            "utilitarian": "Dr. Sam Iqbal",
        }
        for key in default_sprites.keys():
            self.advocate_images[key] = pygame.transform.scale(
                pygame.image.load(f"resources/sprites/{key}.png").convert_alpha(),
                (int(150 * 0.8), int(150 * 0.8)), # Larger size for selection
            )
        
        # For custom advocates, we'll need to decide how to get their image.
        # For now, let's assume they don't have a specific image and we'll use a generic one or just their name.
        # If the custom advocate's name matches a default sprite key, it will use that image.
        # Otherwise, we'll need a placeholder. Let's use 'meritocracy' as a placeholder for now.
        self.placeholder_image = pygame.transform.scale(
            pygame.image.load("resources/sprites/meritocracy.png").convert_alpha(),
            (int(150 * 0.8), int(150 * 0.8)),
        )

        self.advocate_buttons = []
        self.back_button = Button(
            int(20 * 0.8),
            int(20 * 0.8),
            int(100 * 0.8),
            int(50 * 0.8),
            "Back",
        )

        self.scroll_offset = 0
        self.item_height = int(200 * 0.8) # Height of each advocate item (image + text)
        self.padding = int(20 * 0.8)
        self._create_advocate_buttons()

    def _create_advocate_buttons(self):
        self.advocate_buttons = []
        start_x = self.screen_width / 2 - int(200 * 0.8) # Center the buttons
        start_y = int(150 * 0.8) # Below the title

        for i, advocate_profile in enumerate(self.custom_advocates):
            key = advocate_profile.name # Use advocate name as key
            # Create a "button" area for each advocate
            button_rect = pygame.Rect(
                start_x,
                start_y + i * (self.item_height + self.padding),
                int(400 * 0.8),
                self.item_height,
            )
            self.advocate_buttons.append({"key": key, "name": advocate_profile.name, "rect": button_rect})

    def handle_event(self, event):
        if self.back_button.is_clicked(event):
            return "back"

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for advocate_btn in self.advocate_buttons:
                # Adjust for scroll offset when checking click
                adjusted_rect = advocate_btn["rect"].copy()
                adjusted_rect.y -= self.scroll_offset
                if adjusted_rect.collidepoint(event.pos):
                    return advocate_btn["key"]

        if event.type == pygame.MOUSEWHEEL:
            self.scroll_offset -= event.y * 10
            self._clamp_scroll()
        return None

    def _clamp_scroll(self):
        content_height = len(self.advocates_data) * (self.item_height + self.padding)
        max_scroll = max(0, content_height - (self.screen_height - int(200 * 0.8))) # Max scrollable area
        if self.scroll_offset < 0:
            self.scroll_offset = 0
        if self.scroll_offset > max_scroll:
            self.scroll_offset = max_scroll

    def draw(self, screen):
        screen.fill((30, 30, 60)) # Darker blue background

        title_surface = self.font_title.render("Select Your Advocate", True, (255, 255, 255))
        screen.blit(title_surface, (self.screen_width / 2 - title_surface.get_width() / 2, int(50 * 0.8)))

        # Draw advocate buttons
        for advocate_btn in self.advocate_buttons:
            rect = advocate_btn["rect"].copy()
            rect.y -= self.scroll_offset

            # Only draw if visible on screen
            if rect.bottom > int(100 * 0.8) and rect.top < self.screen_height:
                pygame.draw.rect(screen, (50, 50, 100), rect, border_radius=10) # Button background
                pygame.draw.rect(screen, (100, 100, 200), rect, 2, border_radius=10) # Border

                # Draw image
                image = self.advocate_images.get(advocate_btn["key"], self.placeholder_image) # Use specific image or placeholder
                image_rect = image.get_rect(center=(rect.centerx, rect.y + int(rect.height * 0.4)))
                screen.blit(image, image_rect)

                # Draw name
                name_surface = self.font_advocate.render(advocate_btn["name"], True, (255, 255, 255))
                name_rect = name_surface.get_rect(center=(rect.centerx, rect.y + int(rect.height * 0.8)))
                screen.blit(name_surface, name_rect)

        self.back_button.draw(screen)


class ChatGUI:
    def __init__(self, agents, screen_width, screen_height, selected_advocate_key=None, num_custom_advocates=0):
        self.screen_width = screen_width
        self.screen_height = screen_height
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
        self.selected_advocate_key = selected_advocate_key # Store the selected advocate key
        self.chat_history = [
            "Please select who you would want to talk to...",
        ]
        self.current_chat_index = 0
        self.chat_scroll_offset = 0
        self.chat_scrollbar_width = int(15 * 0.8)
        self.dragging_chat_scrollbar = False
        input_box_x = int((1560 - 40 - 500) * 0.8)
        input_box_y = int(40 * 0.8)
        input_box_width = int(500 * 0.8)
        input_box_height = int(self.screen_height * 0.2)
        
        self.main_input_box = TextInputBox(
            input_box_x, input_box_y, input_box_width, input_box_height, pygame.font.Font("resources/roboto_fonts/Roboto-Regular.ttf", int(24 * 0.8)), placeholder="(ask a question or tell a story about justice...)"
        )
        self.submit_button = Button(
            input_box_x + input_box_width - int(120 * 0.8), input_box_y + input_box_height + int(10 * 0.8), int(120 * 0.8), int(40 * 0.8), "Submit"
        )
        self.create_advocate_button = Button(
            self.screen_width - int(220 * 0.8), self.screen_height - int(60 * 0.8), int(200 * 0.8), int(40 * 0.8), "Create Advocate"
        )
        self.num_custom_advocates = num_custom_advocates
        self.select_custom_advocate_button = Button(
            self.screen_width - int(220 * 0.8), self.screen_height - int(110 * 0.8), int(200 * 0.8), int(40 * 0.8), "Select Custom"
        )
        self.prev_button = Button(self.dialogue_box_rect.x - int(60 * 0.8), self.dialogue_box_rect.centery - int(20 * 0.8), int(50 * 0.8), int(40 * 0.8), "<")
        self.next_button = Button(self.dialogue_box_rect.right + int(10 * 0.8), self.dialogue_box_rect.centery - int(20 * 0.8), int(50 * 0.8), int(40 * 0.8), ">")
        self.checkboxes = self._create_checkboxes()
        self.checkbox_label = pygame.font.Font("resources/roboto_fonts/Roboto-Regular.ttf", int(24 * 0.8)).render("Select the character(s) you would like to talk to:", True, (0, 0, 0))


    def _create_checkboxes(self):
        checkboxes = []
        x, y = int(40 * 0.8), int(80 * 0.8)
        for agent_name, agent_obj in self.agents.items():
            is_on = (agent_name == self.selected_advocate_key) # Pre-select if it matches
            checkboxes.append(CheckBox(x, y, int(20 * 0.8), int(20 * 0.8), agent_obj.profile.name, is_on=is_on))
            y += int(40 * 0.8)
        return checkboxes

    def handle_event(self, event):
        self.main_input_box.handle_event(event)
        for checkbox in self.checkboxes:
            checkbox.handle_event(event)

        if self.prev_button.is_clicked(event):
            if self.current_chat_index > 0:
                self.current_chat_index -= 1
                while self.current_chat_index > 0 and self.chat_history[self.current_chat_index].startswith("You:"):
                    self.current_chat_index -= 1
        if self.next_button.is_clicked(event):
            if self.current_chat_index < len(self.chat_history) - 1:
                self.current_chat_index += 1
                while self.current_chat_index < len(self.chat_history) - 1 and self.chat_history[self.current_chat_index].startswith("You:"):
                    self.current_chat_index += 1

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
        
        if self.num_custom_advocates > 0 and self.select_custom_advocate_button.is_clicked(event):
            return "select_advocate"

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
        return render_wrapped_text(self.chat_history[self.current_chat_index], self.font, (0,0,0), self.dialogue_box_rect, self.screen, get_height=True)

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

        if self.chat_history:
            # Display the current message from the history
            message = self.chat_history[self.current_chat_index]
            
            # Define bubble properties
            bubble_rect = self.dialogue_box_rect
            bubble_color = (255, 255, 255)
            text_color = (0, 0, 0)
            
            # Determine tail position based on who is speaking
            if message.startswith("You:"):
                tail_pos = (bubble_rect.right - 20, bubble_rect.bottom)
            else:
                agent_name = message.split(":")[0]
                if agent_name in self.sprites:
                    sprite_pos = self._get_sprite_pos(agent_name)
                    tail_pos = (sprite_pos[0] + 30, bubble_rect.top)
                else:
                    tail_pos = (bubble_rect.left + 20, bubble_rect.top)

            draw_speech_bubble(screen, message, self.font, text_color, bubble_color, bubble_rect, tail_pos)

        self.prev_button.draw(screen)
        self.next_button.draw(screen)

        self.main_input_box.draw(screen)
        self.submit_button.draw(screen)
        self.create_advocate_button.draw(screen)
        if self.num_custom_advocates > 0:
            self.select_custom_advocate_button.draw(screen)
        
        screen.blit(self.checkbox_label, (int(40 * 0.8), int(40 * 0.8)))
        for checkbox in self.checkboxes:
            checkbox.draw(screen)

        self._draw_sprites(screen)

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


# --- Utility Functions ---


def draw_speech_bubble(surface, text, font, text_color, bubble_color, rect, tail_pos):
    # Draw the bubble
    pygame.draw.rect(surface, bubble_color, rect, border_radius=10)
    
    # Draw the tail
    pygame.draw.polygon(surface, bubble_color, [tail_pos, (tail_pos[0] - 10, tail_pos[1] + 10), (tail_pos[0] + 10, tail_pos[1] + 10)])

    render_wrapped_text(text, font, text_color, rect, surface)

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
