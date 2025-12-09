import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import subprocess, sys, os, threading, re

# Optional HTML preview engine
try:
    from tkinterweb import HtmlFrame
except:
    HtmlFrame = None


class MiniIDLE(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("FysonWorks – Caleb's IDLE")
        self.geometry("1100x700")
        self.configure(bg="#0d0d0d")

        # State
        self._filename = None
        self.current_language = "Python"
        self.preview_frame = None
        self.preview_widget = None
        self._preview_after = None
        self.chunk_window = None
        self.code_chunks = []
        self.image_window = None
        self.image_listbox = None
        self.image_folder = None

        # Snippet folders
        self.snippet_folder = os.path.join(os.getcwd(), "snippets")
        os.makedirs(self.snippet_folder, exist_ok=True)
        os.makedirs(os.path.join(self.snippet_folder, "python"), exist_ok=True)
        os.makedirs(os.path.join(self.snippet_folder, "html"), exist_ok=True)

        # Built-in snippets
        self.BUILTIN_SNIPPETS = {
            "python": {
                "forloop": "for i in range():\n    pass\n",
                "func": "def function_name():\n    pass\n",
                "class": "class NewClass:\n    def __init__(self):\n        pass\n"
            },
            "html": {
                "div": "<div></div>",
                "h1": "<h1>Title</h1>",
                "button": "<button>Click</button>",
                "page": (
                    "<!DOCTYPE html>\n<html>\n<head>\n<title>New Page</title>\n</head>\n"
                    "<body>\n\n</body>\n</html>"
                )
            }
        }

        # Theme colors
        self.COLOR_BG = "#111111"
        self.COLOR_PANEL = "#0d0d0d"
        self.COLOR_PANEL_DARK = "#161616"
        self.COLOR_ACCENT = "#2a2a2a"
        self.COLOR_ACCENT_HOVER = "#3a3a3a"
        self.COLOR_TEXT = "#e0e0e0"
        self.COLOR_MUTED = "#6a6a6a"
        self.COLOR_OUTPUT_BG = "#0e0e0e"
        self.COLOR_OUTPUT_TEXT = "#11dd66"
        self.COLOR_LINENO_BG = "#111111"
        self.COLOR_LINENO_TEXT = "#555555"

        self.code_font = ("Consolas", 11)
        self.ui_font = ("Segoe UI", 10)

        # Build UI
        self._create_widgets()
        self._create_menu()

        self.append_output("FysonWorks – Caleb's IDLE ready.\n")

    # ======================================================
    #                 OUTPUT + LOGGING
    # ======================================================
    def append_output(self, text):
        self.output.config(state="normal")
        self.output.insert(tk.END, text)
        self.output.see(tk.END)
        self.output.config(state="disabled")

    # ======================================================
    #                 LINE NUMBER SYSTEM
    # ======================================================
    def _update_line_numbers(self):
        self.linenumbers.config(state="normal")
        self.linenumbers.delete("1.0", tk.END)

        line_count = int(self.text.index("end-1c").split(".")[0])
        lineno_text = "\n".join(str(i) for i in range(1, line_count + 1))

        self.linenumbers.insert("1.0", lineno_text)
        self.linenumbers.config(state="disabled")

    def _on_scrollbar(self, *args):
        self.text.yview(*args)
        self.linenumbers.yview(*args)

    def _on_textscroll(self, *args):
        self.y_scroll.set(*args)
        self.linenumbers.yview_moveto(args[0])

    # ======================================================
    #              SYNTAX HIGHLIGHT (BASIC)
    # ======================================================
    def _highlight_syntax(self):
        self.text.tag_remove("keyword", "1.0", tk.END)
        self.text.tag_remove("string", "1.0", tk.END)
        self.text.tag_remove("tag", "1.0", tk.END)

        content = self.text.get("1.0", tk.END)

        # Python
        if self.current_language == "Python":
            keywords = r"\b(def|class|for|while|if|elif|else|try|except|return|import|from|as|with|pass|in|not|and|or)\b"
            for match in re.finditer(keywords, content):
                start = f"1.0+{match.start()}c"
                end = f"1.0+{match.end()}c"
                self.text.tag_add("keyword", start, end)

            self.text.tag_config("keyword", foreground="#5ea2ff")

            # strings
            for match in re.finditer(r"(\".*?\"|\'.*?\')", content):
                start = f"1.0+{match.start()}c"
                end = f"1.0+{match.end()}c"
                self.text.tag_add("string", start, end)

            self.text.tag_config("string", foreground="#ffcc66")

        # HTML
        if self.current_language == "HTML":
            for match in re.finditer(r"<[^>]+>", content):
                start = f"1.0+{match.start()}c"
                end = f"1.0+{match.end()}c"
                self.text.tag_add("tag", start, end)

            self.text.tag_config("tag", foreground="#66d9ef")

    # ======================================================
    #           HTML PREVIEW UPDATE HANDLING
    # ======================================================
    def _update_preview_visibility(self):
        if self.current_language == "HTML":
            self.preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        else:
            self.preview_frame.pack_forget()

    def _update_html_preview(self):
        if self.current_language != "HTML":
            return

        html_code = self.text.get("1.0", tk.END)

        if HtmlFrame:
            try:
                self.preview_widget.load_html(html_code)
            except:
                pass  # ignore preview errors
        else:
            self.preview_widget.config(state="normal")
            self.preview_widget.delete("1.0", tk.END)
            self.preview_widget.insert("1.0", html_code)
            self.preview_widget.config(state="disabled")

    # ======================================================
    #        MAIN TEXT-CHANGE EVENT (HIGHLIGHT + PREVIEW)
    # ======================================================
    def _on_text_change(self, event=None):
        self._highlight_syntax()
        self._update_line_numbers()

        # HTML preview throttle
        if self.current_language == "HTML":
            if self._preview_after:
                self.after_cancel(self._preview_after)
            self._preview_after = self.after(300, self._update_html_preview)

    # ======================================================
    #                     FILE OPERATIONS
    # ======================================================
    def new_file(self):
        self.text.delete("1.0", tk.END)
        self._filename = None
        self.current_language = "Python"
        self.title("FysonWorks – Caleb's IDLE (Python)")
        self._update_preview_visibility()
        self.append_output("New file created.\n")

    def open_file(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("Python Files", "*.py"),
                ("HTML Files", "*.html"),
                ("All Files", "*.*")
            ]
        )
        if not path:
            return

        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", text)
        self._filename = path

        if path.endswith(".html"):
            self.current_language = "HTML"
        else:
            self.current_language = "Python"

        self.title(f"FysonWorks – Caleb's IDLE ({self.current_language})")
        self._update_preview_visibility()
        self._highlight_syntax()
        self._update_line_numbers()
        self.append_output(f"Opened: {path}\n")

    def save_file(self):
        if not self._filename:
            return self.save_file_as()

        with open(self._filename, "w", encoding="utf-8") as f:
            f.write(self.text.get("1.0", tk.END))

        self.append_output(f"Saved: {self._filename}\n")

    def save_file_as(self):
        ext = ".html" if self.current_language == "HTML" else ".py"

        path = filedialog.asksaveasfilename(defaultextension=ext)
        if not path:
            return

        self._filename = path
        self.save_file()

    # ======================================================
    #                  RUN PYTHON + HTML
    # ======================================================
    def run_code(self):
        code = self.text.get("1.0", tk.END).strip()

        if not code:
            self.append_output("Nothing to run.\n")
            return

        if self.current_language == "Python":
            self._run_python(code)
        elif self.current_language == "HTML":
            self._run_html(code)
        else:
            self.append_output("Run only supports Python and HTML.\n")

    def _run_python(self, code):
        temp = "__run_temp__.py"

        with open(temp, "w", encoding="utf-8") as f:
            f.write(code)

        def runner():
            try:
                proc = subprocess.Popen(
                    [sys.executable, temp],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                for line in proc.stdout:
                    self.append_output(line)
            except Exception as e:
                self.append_output(f"[Python Error] {e}\n")

        threading.Thread(target=runner, daemon=True).start()

    def _run_html(self, code):
        temp = "__run_temp__.html"

        with open(temp, "w", encoding="utf-8") as f:
            f.write(code)

        import webbrowser
        webbrowser.open("file://" + os.path.abspath(temp))
        self.append_output("Opened HTML in browser.\n")

    # ======================================================
    #                   SNIPPET SYSTEM
    # ======================================================
    def add_snippet(self):
        try:
            selected = self.text.get(tk.SEL_FIRST, tk.SEL_LAST)
        except:
            messagebox.showinfo("Snippet", "Select text first.")
            return

        name = simpledialog.askstring("Snippet Name", "Enter snippet name:")
        if not name:
            return

        lang = self.current_language.lower()
        folder = os.path.join(self.snippet_folder, lang)
        os.makedirs(folder, exist_ok=True)

        with open(os.path.join(folder, name + ".txt"), "w", encoding="utf-8") as f:
            f.write(selected)

        messagebox.showinfo("Snippet", f"Snippet '{name}' saved!")

    def load_snippets(self):
        lang = self.current_language.lower()
        folder = os.path.join(self.snippet_folder, lang)

        snips = dict(self.BUILTIN_SNIPPETS.get(lang, {}))

        for f in os.listdir(folder):
            if f.endswith(".txt"):
                with open(os.path.join(folder, f), "r", encoding="utf-8") as file:
                    snips[f[:-4]] = file.read()

        return snips

    def open_snippet_window(self):
        snips = self.load_snippets()

        win = tk.Toplevel(self)
        win.title("Snippets")
        win.geometry("350x420")
        win.configure(bg=self.COLOR_PANEL)

        tk.Label(
            win,
            text=f"{self.current_language} Snippets",
            bg=self.COLOR_PANEL,
            fg=self.COLOR_TEXT,
            font=("Segoe UI Semibold", 12)
        ).pack(pady=8)

        box = tk.Listbox(
            win,
            bg="#101010",
            fg=self.COLOR_TEXT,
            activestyle="none",
            font=("Consolas", 11)
        )
        box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for key in sorted(snips):
            box.insert(tk.END, key)

        def insert():
            sel = box.curselection()
            if sel:
                snippet = snips[box.get(sel[0])]
                self.text.insert(tk.INSERT, snippet)

        tk.Button(
            win,
            text="Insert Snippet",
            command=insert,
            bg=self.COLOR_ACCENT,
            fg=self.COLOR_TEXT,
            relief=tk.FLAT,
            padx=10, pady=4
        ).pack(pady=8)

    # ======================================================
    #                IMAGE MANAGER WINDOW
    # ======================================================
    def open_image_manager(self):
        if self.image_window and self.image_window.winfo_exists():
            self.image_window.lift()
            return

        self.image_folder = os.path.join(os.getcwd(), "assets")
        os.makedirs(self.image_folder, exist_ok=True)

        win = tk.Toplevel(self)
        self.image_window = win
        win.title("Image Manager")
        win.geometry("420x500")
        win.configure(bg=self.COLOR_PANEL)

        tk.Label(
            win,
            text="Image Manager",
            bg=self.COLOR_PANEL,
            fg=self.COLOR_TEXT,
            font=("Segoe UI Semibold", 12)
        ).pack(pady=8)

        tk.Button(
            win,
            text="Add Image",
            bg=self.COLOR_ACCENT,
            fg=self.COLOR_TEXT,
            relief=tk.FLAT,
            padx=10, pady=4,
            command=self._add_image
        ).pack(fill=tk.X, padx=10, pady=8)

        frame = tk.Frame(win, bg=self.COLOR_PANEL)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.image_listbox = tk.Listbox(
            frame,
            bg="#101010",
            fg=self.COLOR_TEXT,
            font=("Consolas", 10),
            activestyle="none",
            selectbackground="#333333"
        )
        self.image_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.image_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.image_listbox.yview)

        self.image_listbox.bind("<Double-Button-1>", self._insert_image_path)

        self._refresh_image_list()

    def _add_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.gif;*.webp")]
        )
        if not path:
            return

        filename = os.path.basename(path)
        dest = os.path.join(self.image_folder, filename)

        base, ext = os.path.splitext(filename)
        i = 1

        while os.path.exists(dest):
            dest = os.path.join(self.image_folder, f"{base}_{i}{ext}")
            i += 1

        with open(path, "rb") as src, open(dest, "wb") as dst:
            dst.write(src.read())

        self._refresh_image_list()

    def _refresh_image_list(self):
        self.image_listbox.delete(0, tk.END)

        for f in os.listdir(self.image_folder):
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                self.image_listbox.insert(tk.END, f)

    def _insert_image_path(self, event=None):
        sel = self.image_listbox.curselection()
        if not sel:
            return

        filename = self.image_listbox.get(sel[0])
        full_path = os.path.join(self.image_folder, filename)

        self.text.insert(tk.INSERT, f'"{full_path}"')

    # ======================================================
    #                     CHUNK EDITOR
    # ======================================================
    def open_chunk_editor(self):
        amount = simpledialog.askinteger(
            "Chunks",
            "How many chunks do you want?",
            minvalue=1,
            maxvalue=20
        )
        if not amount:
            return

        # Close old window
        if self.chunk_window and self.chunk_window.winfo_exists():
            self.chunk_window.destroy()

        win = tk.Toplevel(self)
        self.chunk_window = win
        win.title("Chunk Editor")
        win.geometry("700x500")
        win.configure(bg=self.COLOR_PANEL)

        tk.Label(
            win,
            text="Enter code chunks below. Click 'Stitch → Editor' when done.",
            bg=self.COLOR_PANEL,
            fg=self.COLOR_TEXT
        ).pack(pady=8)

        # Scrollable chunk container
        container = tk.Frame(win, bg=self.COLOR_PANEL)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        canvas = tk.Canvas(container, bg=self.COLOR_PANEL, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=self.COLOR_PANEL)

        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.code_chunks = []

        for i in range(amount):
            frame = tk.LabelFrame(
                inner,
                text=f"Chunk {i+1}",
                bg=self.COLOR_PANEL,
                fg=self.COLOR_MUTED,
                bd=1,
                relief=tk.SOLID
            )
            frame.pack(fill=tk.X, padx=6, pady=6)

            txt = tk.Text(
                frame,
                height=4,
                bg=self.COLOR_BG,
                fg=self.COLOR_TEXT,
                insertbackground=self.COLOR_TEXT,
                font=self.code_font,
                relief=tk.FLAT,
                padx=6,
                pady=4
            )
            txt.pack(fill=tk.BOTH, expand=True)

            self.code_chunks.append(txt)

        # Stitch button
        tk.Button(
            win,
            text="Stitch → Editor",
            bg=self.COLOR_ACCENT,
            fg=self.COLOR_TEXT,
            relief=tk.FLAT,
            padx=12,
            pady=5,
            command=self.stitch_chunks
        ).pack(pady=10)

    def stitch_chunks(self):
        """Merge all chunks into the main editor."""
        parts = []

        for txt in self.code_chunks:
            block = txt.get("1.0", tk.END).strip()
            if block:
                parts.append(block)

        if not parts:
            messagebox.showinfo("Chunks", "No chunks to stitch.")
            return

        merged = "\n\n".join(parts)

        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", merged)

        self._update_line_numbers()
        self._highlight_syntax()

        self.append_output("Chunks stitched into main editor.\n")

    # ======================================================
    #         MAIN EDITOR UI (NO TOOLBAR)
    # ======================================================
    def _create_widgets(self):
        root = tk.Frame(self, bg=self.COLOR_PANEL)
        root.pack(fill=tk.BOTH, expand=True)

        # ---------------- MAIN AREA ----------------
        main = tk.Frame(root, bg=self.COLOR_PANEL)
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 4))

        # ----- Line Numbers -----
        self.linenumbers = tk.Text(
            main,
            width=4,
            bg=self.COLOR_LINENO_BG,
            fg=self.COLOR_LINENO_TEXT,
            font=self.code_font,
            state="disabled",
            border=0,
            padx=4
        )
        self.linenumbers.pack(side=tk.LEFT, fill=tk.Y)

        # ----- Text Editor -----
        editor_frame = tk.Frame(main, bg=self.COLOR_PANEL)
        editor_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.text = tk.Text(
            editor_frame,
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            insertbackground=self.COLOR_TEXT,
            font=self.code_font,
            undo=True,
            relief=tk.FLAT,
            border=0,
            padx=6,
            pady=4
        )
        self.text.pack(fill=tk.BOTH, expand=True)

        # Scrollbar
        self.y_scroll = tk.Scrollbar(main, orient="vertical", command=self._on_scrollbar)
        self.y_scroll.pack(side=tk.LEFT, fill=tk.Y)
        self.text.config(yscrollcommand=self._on_textscroll)

        # ----- HTML Preview Panel -----
        self.preview_frame = tk.Frame(main, bg=self.COLOR_PANEL)

        if HtmlFrame is not None:
            self.preview_widget = HtmlFrame(self.preview_frame, messages_enabled=False)
            self.preview_widget.pack(fill=tk.BOTH, expand=True)
        else:
            self.preview_widget = tk.Text(
                self.preview_frame,
                bg=self.COLOR_OUTPUT_BG,
                fg=self.COLOR_TEXT,
                state="disabled",
                font=self.code_font
            )
            self.preview_widget.pack(fill=tk.BOTH, expand=True)

        self.preview_frame.pack_forget()

        # ---------------- OUTPUT WINDOW ----------------
        bottom = tk.Frame(root, bg=self.COLOR_PANEL_DARK)
        bottom.pack(fill=tk.X, padx=8, pady=(0, 4))

        tk.Label(
            bottom,
            text="Output:",
            bg=self.COLOR_PANEL_DARK,
            fg=self.COLOR_MUTED
        ).pack(anchor="w")

        self.output = tk.Text(
            bottom,
            height=6,
            bg=self.COLOR_OUTPUT_BG,
            fg=self.COLOR_OUTPUT_TEXT,
            font=self.code_font,
            relief=tk.FLAT,
            border=0,
            state="disabled",
            padx=6,
            pady=4
        )
        self.output.pack(fill=tk.X)

        # typing event handler
        self.text.bind("<KeyRelease>", self._on_text_change)

        # initialize
        self._update_line_numbers()
        self._update_preview_visibility()

    # ======================================================
    #                   LANGUAGE SELECTOR
    # ======================================================
    def open_language_selector(self):
        win = tk.Toplevel(self)
        win.title("Select Language")
        win.geometry("260x160")
        win.configure(bg=self.COLOR_PANEL)

        tk.Label(
            win,
            text="Choose coding language:",
            bg=self.COLOR_PANEL,
            fg=self.COLOR_TEXT,
            font=("Segoe UI Semibold", 12)
        ).pack(pady=10)

        def choose(lang):
            self.current_language = lang
            self.title(f"FysonWorks – Caleb's IDLE ({lang})")
            self._highlight_syntax()
            self._update_preview_visibility()
            win.destroy()

        tk.Button(
            win,
            text="Python",
            command=lambda: choose("Python"),
            bg=self.COLOR_ACCENT,
            fg=self.COLOR_TEXT,
            relief=tk.FLAT,
            padx=10,
            pady=5
        ).pack(fill=tk.X, padx=20, pady=5)

        tk.Button(
            win,
            text="HTML",
            command=lambda: choose("HTML"),
            bg=self.COLOR_ACCENT,
            fg=self.COLOR_TEXT,
            relief=tk.FLAT,
            padx=10,
            pady=5
        ).pack(fill=tk.X, padx=20, pady=5)

    # ======================================================
    #                       MENU BAR
    # ======================================================
    def _create_menu(self):
        menubar = tk.Menu(self)

        # FILE
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="New", command=self.new_file)
        filemenu.add_command(label="Open...", command=self.open_file)
        filemenu.add_separator()
        filemenu.add_command(label="Save", command=self.save_file)
        filemenu.add_command(label="Save As...", command=self.save_file_as)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=filemenu)

        # EDIT
        editmenu = tk.Menu(menubar, tearoff=0)
        editmenu.add_command(label="Add Snippet", command=self.add_snippet)
        editmenu.add_command(label="Snippet Library", command=self.open_snippet_window)
        editmenu.add_separator()
        editmenu.add_command(label="Chunk Editor", command=self.open_chunk_editor)
        menubar.add_cascade(label="Edit", menu=editmenu)

        # TOOLS (Run lives here)
        toolsmenu = tk.Menu(menubar, tearoff=0)
        toolsmenu.add_command(label="Run", command=self.run_code)
        toolsmenu.add_separator()
        toolsmenu.add_command(label="Image Manager", command=self.open_image_manager)
        toolsmenu.add_command(label="Language Selector", command=self.open_language_selector)
        menubar.add_cascade(label="Tools", menu=toolsmenu)

        # HELP
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=helpmenu)

        self.config(menu=menubar)

    # ======================================================
    #                      ABOUT WINDOW
    # ======================================================
    def _show_about(self):
        messagebox.showinfo(
            "About Caleb's IDLE",
            "FysonWorks – Caleb's IDLE\n\n"
            "Features:\n"
            "• Python + HTML Support\n"
            "• HTML Live Preview\n"
            "• Chunk Editor\n"
            "• Snippets\n"
            "• Image Manager\n"
            "• Full Dark Theme\n"
            "• No Toolbar (clean mode)"
        )
if __name__ == "__main__":
    app = MiniIDLE()
    app.mainloop()
