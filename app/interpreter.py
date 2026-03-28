import math
import operator
import re
import time

# Unterstützte Operatoren für Berechnungen
OPS = {
    "^": operator.pow,
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
}

FUNCTIONS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "exp": math.exp,
}

CONSTANTS = {
    "pi": math.pi,
    "π": math.pi,
    "e": math.e,
}

def make_user_function(interpreter, arglist, expr):
        def user_func(*actuals):
            local_vars = dict(zip(arglist, actuals))
            return interpreter.eval_expr_with_scope(expr, local_vars)
        return user_func

class RetroInterpreter:
    def __init__(self):
        self.functions = {}  # Name -> (arg_list, body_expr)
        self.env = {}  # Variablen speichern
        self.in_if_block = False
        self.if_condition = None
        self.if_lines_true = []
        self.if_lines_false = []
        self.collecting_else = False
        self.in_while_block = False
        self.while_condition = None
        self.while_lines = []
        self.in_for_block = False
        self.for_var = None
        self.for_start = None
        self.for_end = None
        self.for_step = 1
        self.for_lines = []
        self.pending_input_var = None  # Für GUI-Input
        self.last_input_result = None
        self.in_frame_block = False
        self.current_frame = []
        self.frames = []
        # Zusätzliche eingebaute Funktionen für Listen und Strings
        self.builtin_functions = {
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'list': list,
            'ord': ord,
            'chr': chr,
        }

    def run_line(self, line):
        # Falls auf Eingabe gewartet wird, keine weiteren Zeilen ausführen
        if self.pending_input_var is not None:
            return {"input_request": self.pending_input_var}

        # Falls Zeile mehrere Zeilen enthält, einzeln ausführen und Ausgaben mit Zeilenumbruch verbinden
        if isinstance(line, str) and '\n' in line:
            outputs = []
            for subline in line.split('\n'):
                out = self.run_line(subline)
                if out:
                    outputs.append(str(out))
            return "\n".join(outputs)

        line = line.strip()
        # Kommentare ignorieren
        if not line or line.startswith('#'):
            return ""

        # Grafikbefehle im Frame sammeln (ohne Rekursion!)
        if self.in_frame_block:
            cmd = line.upper().split()[0]
            args = line[len(cmd):].strip().split(',')
            try:
                if cmd == "POINT" and len(args) == 2:
                    x = float(self.eval_expr(args[0]))
                    y = float(self.eval_expr(args[1]))
                    self.current_frame.append({"type": "point", "x": x, "y": y})
                elif cmd == "LINE" and len(args) == 4:
                    x1 = float(self.eval_expr(args[0]))
                    y1 = float(self.eval_expr(args[1]))
                    x2 = float(self.eval_expr(args[2]))
                    y2 = float(self.eval_expr(args[3]))
                    self.current_frame.append({"type": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2})
                elif cmd == "CIRCLE" and len(args) == 3:
                    x = float(self.eval_expr(args[0]))
                    y = float(self.eval_expr(args[1]))
                    r = float(self.eval_expr(args[2]))
                    self.current_frame.append({"type": "circle", "x": x, "y": y, "r": r})
                else:
                    return f"Syntax Error in {cmd}"
            except Exception as e:
                return f"Error in {cmd}: {e}"
            return ""

        if self.in_for_block:
            if line.upper() == "NEXT":
                return self._run_for_block()
            else:
                self.for_lines.append(line)
                return ""

        if line.upper().startswith("FOR "):
            return self._start_for_block(line)

        if self.in_while_block:
            if line.upper() == "ENDWHILE":
                return self._run_while_block()
            else:
                self.while_lines.append(line)
                return ""

        # Schleifenbeginn
        if line.upper().startswith("WHILE "):
            return self._start_while_block(line)

        if self.in_if_block:
            if line.upper() == "ELSE":
                self.collecting_else = True
                return ""
            elif line.upper() == "ENDIF":
                return self._run_if_block()
            else:
                if self.collecting_else:
                    self.if_lines_false.append(line)
                else:
                    self.if_lines_true.append(line)
                return ""

        if line.upper().startswith("IF "):
            return self._start_if_block(line)

        if line.upper() == "HELP":
            return self._handle_help()

        if line.upper().startswith("INPUT "):
            return self.handle_input(line[6:].strip())

        if line.upper().startswith("LET "):
            return self.handle_assignment(line[4:].strip())

        elif line.upper().startswith("PRINT "):
            return self.handle_print(line[6:].strip())

        elif line.upper().startswith("DEF "):
            return self.handle_function_def(line[4:].strip())

        else:
            return self.eval_expr(line)

    def _handle_help(self):
        return (
            "Retro Notebook Help:\n"
            "LET var = expr             - Assign value to variable\n"
            "LET arr = [1, 2, 3]        - Create a list/array\n"
            "LET arr[index] = expr      - Assign value to array element\n"
            "LET s = \"Hallo\"           - Create a string\n"
            "LET s[index] = 'X'         - Replace character at index in string\n"
            "PRINT expr                 - Evaluate and print expression\n"
            "INPUT var                  - Ask for user input\n"
            "DEF f(x) = expr            - Define a function\n"
            "IF cond THEN ... ELSE ... ENDIF - Conditional execution\n"
            "WHILE cond DO ... ENDWHILE      - While loop\n"
            "FOR i = a TO b [STEP s] ... NEXT - For loop\n"
            "\n"
            "# Graphics:\n"
            "POINT x, y                 - Draw a point at (x, y)\n"
            "LINE x1, y1, x2, y2        - Draw a line from (x1, y1) to (x2, y2)\n"
            "CIRCLE x, y, r             - Draw a circle with center (x, y) and radius r\n"
            "\n"
            "# Built-in functions for lists/strings:\n"
            "len(x)   - Length of list or string\n"
            "str(x)   - Convert to string\n"
            "int(x)   - Convert to integer\n"
            "float(x) - Convert to float\n"
            "list(x)  - Convert to list\n"
            "ord(c)   - Unicode code of character\n"
            "chr(n)   - Character from Unicode code\n"
            "\n"
            "# Notes:\n"
            "- All graphics commands in a code block are shown together.\n"
            "- WHILE/ENDWHILE and FOR/NEXT support blocks.\n"
            "- Errors in loops or graphics abort execution.\n"
            "- Max 1000 WHILE iterations (to prevent endless loops).\n"
            "\n"
            "HELP                        - Show this help message"
        )

    def _start_for_block(self, line):
            match = re.match(r"FOR ([a-zA-Z_][a-zA-Z0-9_]*) = (.+?) TO (.+?)( STEP (.+))?$", line, re.IGNORECASE)
            if not match:
                return "Syntax Error in FOR"

            self.in_for_block = True
            self.for_var = match.group(1)
            self.for_start = self.eval_expr(match.group(2))
            self.for_end = self.eval_expr(match.group(3))
            self.for_step = self.eval_expr(match.group(5)) if match.group(5) else 1
            self.for_lines = []

            return ""

    def _run_for_block(self):
        self.in_for_block = False
        outputs = []

        i = self.for_start
        self.env[self.for_var] = i

        cmp = (lambda a, b: a <= b) if self.for_step > 0 else (lambda a, b: a >= b)

        while cmp(i, self.for_end):
            self.env[self.for_var] = i
            for line in self.for_lines:
                out = self.run_line(line)
                if out:
                    outputs.append(out)
            i += self.for_step

        return "\n".join(outputs)

    def _start_while_block(self, line):
        match = re.match(r"WHILE (.+?) DO", line, re.IGNORECASE)
        if not match:
            return "Syntax Error in WHILE"

        self.in_while_block = True
        self.while_condition = match.group(1)
        self.while_lines = []
        return ""
    
    def _run_while_block(self):
        self.in_while_block = False
        outputs = []
        max_loops = 1000
        loop_count = 0
        last_i = None
        while True:
            if loop_count >= max_loops:
                outputs.append("Error: Maximum WHILE loop iterations (1000) exceeded. Possible endless loop.")
                break
            condition_result = self.eval_expr(self.while_condition)
            if isinstance(condition_result, str) and condition_result.startswith("Error"):
                outputs.append(condition_result)
                break
            if not condition_result:
                break
            # Debug: Wert von i ausgeben, falls vorhanden
            debug_i = self.env.get('i', None)
            outputs.append(f"[DEBUG] i = {debug_i}")
            for line in self.while_lines:
                out = self.run_line(line)
                if isinstance(out, list):
                    outputs.extend(out)
                elif out:
                    outputs.append(out)
                # Schleife abbrechen, wenn Fehler erkannt wird
                if isinstance(out, str) and out.startswith("Error"):
                    outputs.append("Aborting WHILE due to error.")
                    return outputs
            # Prüfe, ob sich i verändert hat
            if debug_i == self.env.get('i', None):
                outputs.append("Error: i did not change in this loop iteration. Possible endless loop.")
                break
            loop_count += 1
        return outputs

    def _start_if_block(self, line):
        match = re.match(r"IF (.+?) THEN", line, re.IGNORECASE)
        if not match:
            return "Syntax Error in IF"

        condition = match.group(1)
        self.in_if_block = True
        self.if_condition = condition
        self.if_lines_true = []
        self.if_lines_false = []
        self.collecting_else = False
        return ""  # nichts sofort ausgeben

    def _run_if_block(self):
        self.in_if_block = False
        result = self.eval_expr(self.if_condition)

        if isinstance(result, str) and result.startswith("Error"):
            return result

        lines = self.if_lines_true if result else self.if_lines_false
        outputs = []

        for line in lines:
            out = self.run_line(line)
            if out:
                outputs.append(out)

        return "\n".join(outputs)

    # Funktion zur Handhabung von Funktionsdefinitionen
    def handle_assignment(self, statement):
        # Unterstützt jetzt auch arr[1] = ... und s[1] = ...
        match = re.match(r"([a-zA-Z_][a-zA-Z0-9_]*)(\s*\[\s*(\d+)\s*\])?\s*=\s*(.+)", statement)
        if not match:
            return "Syntax Error in LET"
        name, _, idx, expr = match.groups()
        value = self.eval_expr(expr)
        if idx is not None:
            container = self.env.get(name)
            if isinstance(container, list):
                try:
                    container[int(idx)] = value
                except Exception as e:
                    return f"Error in list assignment: {e}"
                return f"{name}[{idx}] = {value}"
            elif isinstance(container, str):
                try:
                    i = int(idx)
                    if not (0 <= i < len(container)):
                        return f"Error: string index out of range"
                    # Wert muss ein einzelnes Zeichen sein
                    if not (isinstance(value, str) and len(value) == 1):
                        return f"Error: can only assign a single character to string"
                    new_str = container[:i] + value + container[i+1:]
                    self.env[name] = new_str
                    return f"{name}[{idx}] = '{value}'"
                except Exception as e:
                    return f"Error in string assignment: {e}"
            else:
                return f"Error: {name} is not a list or string"
        else:
            self.env[name] = value
            return f"{name} = {value}"

    # Funktion zur Handhabung von PRINT-Anweisungen
    def handle_print(self, expr):
        value = self.eval_expr(expr)
        return f"{value}"

    # Funktion zur Handhabung von Funktionsdefinitionen
    def handle_function_def(self, statement):
        # Beispiel: square(x) = x^2
        match = re.match(r"([a-zA-Z_][a-zA-Z0-9_]*)\((.*?)\)\s*=\s*(.+)", statement)
        if not match:
            return "Syntax Error in DEF"

        name, arg_str, body = match.groups()
        args = [arg.strip() for arg in arg_str.split(",") if arg.strip()]

        self.functions[name] = (args, body)
        return f"Function '{name}' defined"
    
   # Funktion zur Auswertung von Ausdrücken
    def eval_expr(self, expr):
        # Ersetze bekannte Konstanten
        for const, val in CONSTANTS.items():
            expr = re.sub(rf"\b{re.escape(const)}\b", str(val), expr)

        # Ersetze ^ durch ** für Potenzen
        expr = expr.replace("^", "**")

        # Benutzerdefinierte Funktionen
        user_funcs = {}
        for name, (args, body) in self.functions.items():
            user_funcs[name] = make_user_function(self, args, body)

        try:
            safe_globals = {**FUNCTIONS, **user_funcs, **self.env, **self.builtin_functions}
            return eval(expr, {"__builtins__": {}}, safe_globals)
        except Exception as e:
            return f"Error in expression '{expr}': {type(e).__name__}: {e}"

    def eval_expr_with_scope(self, expr, local_vars):
        expr = expr.replace("^", "**")
        for const, val in CONSTANTS.items():
            expr = re.sub(rf"\b{re.escape(const)}\b", str(val), expr)
        try:
            scope = {**FUNCTIONS, **self.env, **local_vars, **self.builtin_functions}
            return eval(expr, {"__builtins__": {}}, scope)
        except Exception as e:
            return f"Error in function expression '{expr}': {type(e).__name__}: {e}"
    
    def handle_input(self, varname):
        varname = varname.strip()
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", varname):
            return "Syntax Error in INPUT"
        self.pending_input_var = varname
        return {"input_request": varname}

    def provide_input(self, value):
        # Setzt den Wert für die zuletzt angeforderte Eingabevariable
        if self.pending_input_var is None:
            return "No input requested."
        varname = self.pending_input_var
        # Versuche, die Eingabe als Zahl zu interpretieren, sonst als String
        try:
            val = float(value) if '.' in str(value) or 'e' in str(value).lower() else int(value)
        except Exception:
            val = value
        self.env[varname] = val
        self.pending_input_var = None
        self.last_input_result = val
        return f"{varname} = {val}"

    def run_block(self, lines):
        outputs = []
        graphics = []
        n = len(lines)
        i = 0
        # Temporär: Grafikbefehle immer sammeln
        collect_graphics = True
        while i < n:
            line = lines[i].strip()
            if not line or line.startswith('#'):
                i += 1
                continue
            # WHILE-Block erkennen
            if line.upper().startswith('WHILE '):
                cond_line = line
                block = []
                i += 1
                depth = 1
                while i < n and depth > 0:
                    l = lines[i].strip()
                    if l.upper().startswith('WHILE '):
                        depth += 1
                    elif l.upper() == 'ENDWHILE':
                        depth -= 1
                        if depth == 0:
                            break
                    block.append(lines[i])
                    i += 1
                # Schleife ausführen, max. 1000 Durchläufe
                loop_count = 0
                while True:
                    if loop_count > 1000:
                        outputs.append('Error: Max WHILE iterations reached')
                        break
                    cond = self.eval_expr(cond_line[6:-2].strip())  # WHILE ... DO
                    if isinstance(cond, str) and cond.startswith('Error'):
                        outputs.append(cond)
                        break
                    if not cond:
                        break
                    # Block ausführen
                    for bline in block:
                        # Grafikbefehle erkennen und sammeln
                        bline_stripped = bline.strip().upper()
                        if collect_graphics and (bline_stripped.startswith('POINT ') or bline_stripped.startswith('LINE ') or bline_stripped.startswith('CIRCLE ')):
                            gobj = self._parse_graphics_command(bline)
                            if gobj:
                                graphics.append(gobj)
                        out = self.run_line(bline)
                        if out and not (isinstance(out, dict) and 'graphics' in out):
                            outputs.append(out)
                        if isinstance(out, str) and out.startswith('Error'):
                            outputs.append('Aborting WHILE due to error.')
                            break
                    loop_count += 1
                i += 1  # nach ENDWHILE
                continue
            # Grafikbefehle erkennen und sammeln
            line_upper = line.upper()
            if collect_graphics and (line_upper.startswith('POINT ') or line_upper.startswith('LINE ') or line_upper.startswith('CIRCLE ')):
                gobj = self._parse_graphics_command(line)
                if gobj:
                    graphics.append(gobj)
                out = self.run_line(line)
                # Fehler- oder leere Ausgaben von Grafikbefehlen NICHT anzeigen
                if out and not (isinstance(out, dict) and 'graphics' in out):
                    if not (isinstance(out, str) and (out.strip() == '' or out.startswith('Syntax Error in') or out.startswith('Error in'))):
                        outputs.append(out)
                i += 1
                continue
            # Normale Zeile
            out = self.run_line(line)
            if out:
                outputs.append(out)
            i += 1
        if graphics:
            outputs.append({'graphics': graphics})
        return outputs

    def _parse_graphics_command(self, line):
        """Hilfsfunktion: Parsen und Auswerten eines Grafikbefehls (POINT, LINE, CIRCLE). Gibt dict zurück oder None bei Fehler."""
        try:
            cmd = line.strip().upper().split()[0]
            args = line.strip()[len(cmd):].strip().split(',')
            if cmd == "POINT" and len(args) == 2:
                x = float(self.eval_expr(args[0]))
                y = float(self.eval_expr(args[1]))
                return {"type": "point", "x": x, "y": y}
            elif cmd == "LINE" and len(args) == 4:
                x1 = float(self.eval_expr(args[0]))
                y1 = float(self.eval_expr(args[1]))
                x2 = float(self.eval_expr(args[2]))
                y2 = float(self.eval_expr(args[3]))
                return {"type": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2}
            elif cmd == "CIRCLE" and len(args) == 3:
                x = float(self.eval_expr(args[0]))
                y = float(self.eval_expr(args[1]))
                r = float(self.eval_expr(args[2]))
                return {"type": "circle", "x": x, "y": y, "r": r}
        except Exception:
            return None
        return None


class DebugSession:
    """Step-by-step debug runner for RetroInterpreter.

    Groups source lines into logical *steps* (single statements, or entire
    block constructs like IF/WHILE/FOR).  The caller can advance one step at
    a time, run until a breakpoint, or abort the session.
    """

    def __init__(self, lines):
        self.lines = lines
        self.breakpoints = set()          # 0-based source line indices
        self._steps = []                  # list of step-dicts built by _analyse
        self._step_idx = 0
        self.current_line = -1            # 0-based source line currently "at"
        self.output_so_far = []
        self.finished = False
        self.interpreter = RetroInterpreter()
        # Flag to distinguish "just started / just resumed from breakpoint"
        # so continue_to_breakpoint does not stop on the current line's own
        # breakpoint marker before executing anything.
        self._just_paused = False

    # ------------------------------------------------------------------
    # Breakpoint management
    # ------------------------------------------------------------------

    def toggle_breakpoint(self, line_idx):
        if line_idx in self.breakpoints:
            self.breakpoints.discard(line_idx)
        else:
            self.breakpoints.add(line_idx)

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def start(self):
        """(Re-)initialise the session ready to execute from the top."""
        self.interpreter = RetroInterpreter()
        self._steps = self._analyse(self.lines)
        self._step_idx = 0
        self.output_so_far = []
        self.finished = False
        self._just_paused = True  # Treat the very first position as "just paused"
        if self._steps:
            self.current_line = self._steps[0]['start_line']
        else:
            self.current_line = -1
            self.finished = True

    # ------------------------------------------------------------------
    # Execution helpers
    # ------------------------------------------------------------------

    def _analyse(self, lines):
        """Split *lines* into logical execution steps."""
        steps = []
        n = len(lines)
        i = 0
        while i < n:
            raw = lines[i]
            stripped = raw.strip()
            if not stripped or stripped.startswith('#'):
                i += 1
                continue

            upper = stripped.upper()
            start = i

            if upper.startswith('WHILE '):
                depth = 1
                j = i + 1
                while j < n and depth > 0:
                    lu = lines[j].strip().upper()
                    if lu.startswith('WHILE '):
                        depth += 1
                    elif lu == 'ENDWHILE':
                        depth -= 1
                    j += 1
                block_end = j

            elif upper.startswith('FOR '):
                depth = 1
                j = i + 1
                while j < n and depth > 0:
                    lu = lines[j].strip().upper()
                    if lu.startswith('FOR '):
                        depth += 1
                    elif lu == 'NEXT':
                        depth -= 1
                    j += 1
                block_end = j

            elif upper.startswith('IF '):
                depth = 1
                j = i + 1
                while j < n and depth > 0:
                    lu = lines[j].strip().upper()
                    if lu.startswith('IF '):
                        depth += 1
                    elif lu == 'ENDIF':
                        depth -= 1
                    j += 1
                    if depth == 0:
                        break
                block_end = j

            elif upper == 'FRAME':
                depth = 1
                j = i + 1
                while j < n and depth > 0:
                    lu = lines[j].strip().upper()
                    if lu == 'FRAME':
                        depth += 1
                    elif lu == 'ENDFRAME':
                        depth -= 1
                    j += 1
                    if depth == 0:
                        break
                block_end = j

            else:
                block_end = i + 1

            steps.append({
                'start_line': start,
                'end_line': block_end,
                'source_lines': lines[start:block_end],
            })
            i = block_end

        return steps

    def _execute_step(self, step):
        """Run one step dict through the interpreter; return list of outputs."""
        results = self.interpreter.run_block(step['source_lines'])
        outputs = []
        for r in results:
            if isinstance(r, list):
                outputs.extend(r)
            elif r:
                outputs.append(r)
        return outputs

    def _make_state(self, event, executed_line, outputs):
        """Build the state dict returned to the UI."""
        return {
            'event': event,
            'executed_line': executed_line,
            'current_line': self.current_line,
            'vars': dict(self.interpreter.env),
            'output': outputs,
            'finished': self.finished,
        }

    # ------------------------------------------------------------------
    # Public step / continue API
    # ------------------------------------------------------------------

    def step(self):
        """Execute the current step and advance to the next.

        Returns a state dict for the UI to consume.
        """
        if self.finished or self._step_idx >= len(self._steps):
            self.finished = True
            return self._make_state('finished', self.current_line, [])

        step = self._steps[self._step_idx]
        exec_line = step['start_line']
        self.current_line = exec_line
        self._just_paused = False

        outputs = self._execute_step(step)
        self.output_so_far.extend(outputs)
        self._step_idx += 1

        if self._step_idx >= len(self._steps):
            self.finished = True
            return self._make_state('finished', exec_line, outputs)

        self.current_line = self._steps[self._step_idx]['start_line']
        self._just_paused = True
        return self._make_state('stepped', exec_line, outputs)

    def continue_to_breakpoint(self):
        """Run steps until a breakpoint is hit or execution finishes.

        Returns a state dict (event='breakpoint' or event='finished').

        Note: when called immediately after :meth:`start` or after stopping at
        a breakpoint (``_just_paused`` is True), the current step's own
        breakpoint marker is skipped so that execution advances at least one
        step before the next pause.  This prevents a "continue" immediately
        re-pausing on the same line the user already stopped at.
        """
        if self.finished or self._step_idx >= len(self._steps):
            self.finished = True
            return self._make_state('finished', self.current_line, [])

        all_outputs = []
        skip_current = self._just_paused
        self._just_paused = False

        while self._step_idx < len(self._steps):
            step = self._steps[self._step_idx]
            exec_line = step['start_line']

            # Pause *before* executing if this line has a breakpoint,
            # but skip the very first check so we advance at least one step.
            if not skip_current and exec_line in self.breakpoints:
                self.current_line = exec_line
                self._just_paused = True
                return self._make_state('breakpoint', exec_line, all_outputs)

            skip_current = False
            self.current_line = exec_line
            outputs = self._execute_step(step)
            self.output_so_far.extend(outputs)
            all_outputs.extend(outputs)
            self._step_idx += 1

        self.finished = True
        self.current_line = self._steps[-1]['start_line'] if self._steps else -1
        return self._make_state('finished', self.current_line, all_outputs)