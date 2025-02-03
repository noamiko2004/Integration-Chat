import msvcrt  # For Windows
import sys
from threading import Lock

class ChatInput:
    def __init__(self):
        self.current_input = []
        self.cursor_pos = 0
        self.input_lock = Lock()
    
    def get_input(self):
        """Get input character by character while maintaining state."""
        while True:
            if msvcrt.kbhit():
                char = msvcrt.getch()
                
                # Handle special keys
                if char in [b'\r', b'\n']:  # Enter key
                    with self.input_lock:
                        message = ''.join(self.current_input)
                        self.current_input = []
                        self.cursor_pos = 0
                        print()  # New line after enter
                        return message
                        
                elif char == b'\x08':  # Backspace
                    with self.input_lock:
                        if self.cursor_pos > 0:
                            self.current_input.pop(self.cursor_pos - 1)
                            self.cursor_pos -= 1
                            # Clear line and rewrite
                            sys.stdout.write('\r' + ' ' * 100 + '\r> ' + ''.join(self.current_input))
                            
                elif char == b'\xe0':  # Arrow keys prefix
                    second_char = msvcrt.getch()
                    with self.input_lock:
                        if second_char == b'K':  # Left arrow
                            if self.cursor_pos > 0:
                                self.cursor_pos -= 1
                        elif second_char == b'M':  # Right arrow
                            if self.cursor_pos < len(self.current_input):
                                self.cursor_pos += 1
                        # Redraw input line with cursor
                        self._redraw_input()
                        
                elif char.isascii():  # Regular character
                    with self.input_lock:
                        char_str = char.decode('ascii')
                        self.current_input.insert(self.cursor_pos, char_str)
                        self.cursor_pos += 1
                        # Clear line and rewrite
                        sys.stdout.write('\r' + ' ' * 100 + '\r> ' + ''.join(self.current_input))

    def _redraw_input(self):
        """Redraw the current input line."""
        sys.stdout.write('\r' + ' ' * 100 + '\r> ' + ''.join(self.current_input))
        # Move cursor to correct position
        if self.cursor_pos < len(self.current_input):
            sys.stdout.write('\033[' + str(len(self.current_input) - self.cursor_pos) + 'D')
        sys.stdout.flush()

    def get_current_input(self):
        """Get the current input buffer."""
        with self.input_lock:
            return ''.join(self.current_input)
    
    def restore_input(self):
        """Restore the current input after screen refresh."""
        with self.input_lock:
            if self.current_input:
                sys.stdout.write('> ' + ''.join(self.current_input))
                sys.stdout.flush()