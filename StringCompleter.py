# http://pymotw.com/2/cmd/
# https://stackoverflow.com/questions/7821661/how-to-code-autocompletion-in-python

import readline

class StringCompleter(object):

    def __init__(self, options):
        self.options = sorted(options)

    def complete(self, text, state):
        # build and cache matches
        if state == 0:
            if text:
                self.matches = [s for s in self.options 
                        if s and s.startswith(text)]
            # no text entered, thus all matches
            else:
                self.matches = self.options[:]
        # return match indexed by state
        try: 
            return self.matches[state]
        except IndexError:
            return None

