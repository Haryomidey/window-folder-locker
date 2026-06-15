"""Tkinter GUI for Windows Folder Locker."""

from __future__ import annotations

import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .auth import AppAuthenticator
from .config import AUTH_FILE
from .errors import FolderNotFoundError, FolderStateError, LockerError
from .factory import create_locker
from .service import FolderLocker


class PasswordDialog(tk.Toplevel):
    """Modal dialog for password entry and confirmation."""

    def __init__(
        self,
        parent: tk.Misc,
        title: str,
        prompt: str,
        confirm: bool = False,
    ) -> None:
        super().__init__(parent)
        self.result: str | tuple[str, str] | None = None
        self._confirm = confirm

        self.title(title)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=18)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text=prompt, style="Muted.TLabel").grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 10),
        )

        ttk.Label(frame, text="Password").grid(row=1, column=0, sticky="w")
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(
            frame,
            textvariable=self.password_var,
            show="*",
            width=34,
        )
        password_entry.grid(row=1, column=1, sticky="ew", pady=4)

        self.confirm_var = tk.StringVar()
        if confirm:
            ttk.Label(frame, text="Confirm").grid(row=2, column=0, sticky="w")
            ttk.Entry(
                frame,
                textvariable=self.confirm_var,
                show="*",
                width=34,
            ).grid(row=2, column=1, sticky="ew", pady=4)

        buttons = ttk.Frame(frame)
        buttons.grid(row=3, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(
            side="right",
            padx=(8, 0),
        )
        ttk.Button(buttons, text="OK", style="Accent.TButton", command=self._ok).pack(
            side="right",
        )

        self.bind("<Return>", lambda _event: self._ok())
        self.bind("<Escape>", lambda _event: self.destroy())
        password_entry.focus_set()
        self.wait_visibility()
        self._center(parent)

    def _ok(self) -> None:
        password = self.password_var.get()
        if not password:
            messagebox.showerror("Password required", "Enter a password.", parent=self)
            return
        if self._confirm:
            confirmation = self.confirm_var.get()
            if password != confirmation:
                messagebox.showerror(
                    "Passwords do not match",
                    "Enter the same password twice.",
                    parent=self,
                )
                return
            self.result = (password, confirmation)
        else:
            self.result = password
        self.destroy()

    def _center(self, parent: tk.Misc) -> None:
        self.update_idletasks()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        width = self.winfo_width()
        height = self.winfo_height()
        x = parent_x + max((parent_w - width) // 2, 0)
        y = parent_y + max((parent_h - height) // 2, 0)
        self.geometry(f"+{x}+{y}")


class ChangePasswordDialog(tk.Toplevel):
    """Modal dialog for changing a password."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        self.result: tuple[str, str] | None = None

        self.title("Change Password")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=18)
        frame.grid(row=0, column=0, sticky="nsew")

        fields = [
            ("Current password", "current"),
            ("New password", "new"),
            ("Confirm new password", "confirm"),
        ]
        self.values: dict[str, tk.StringVar] = {}
        for row, (label, key) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w")
            var = tk.StringVar()
            self.values[key] = var
            ttk.Entry(frame, textvariable=var, show="*", width=34).grid(
                row=row,
                column=1,
                sticky="ew",
                pady=4,
            )

        buttons = ttk.Frame(frame)
        buttons.grid(row=3, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(
            side="right",
            padx=(8, 0),
        )
        ttk.Button(buttons, text="Save", style="Accent.TButton", command=self._ok).pack(
            side="right",
        )

        self.bind("<Return>", lambda _event: self._ok())
        self.bind("<Escape>", lambda _event: self.destroy())
        self.wait_visibility()
        self._center(parent)

    def _ok(self) -> None:
        current = self.values["current"].get()
        new = self.values["new"].get()
        confirmation = self.values["confirm"].get()
        if not current or not new:
            messagebox.showerror("Password required", "Fill in all password fields.")
            return
        if new != confirmation:
            messagebox.showerror("Passwords do not match", "Confirm the new password.")
            return
        self.result = (current, new)
        self.destroy()

    def _center(self, parent: tk.Misc) -> None:
        self.update_idletasks()
        x = parent.winfo_rootx() + max((parent.winfo_width() - self.winfo_width()) // 2, 0)
        y = parent.winfo_rooty() + max((parent.winfo_height() - self.winfo_height()) // 2, 0)
        self.geometry(f"+{x}+{y}")


class FolderLockerApp(tk.Tk):
    """Main Tkinter window."""

    def __init__(self, data_dir: Path) -> None:
        super().__init__()
        self.data_dir = data_dir
        self.authenticator = AppAuthenticator(data_dir / AUTH_FILE)
        self.locker: FolderLocker | None = None
        self.folder_ids: dict[str, str] = {}

        self.title("Windows Folder Locker")
        self.geometry("920x580")
        self.minsize(760, 480)
        self.configure(bg="#f4f7fb")

        self._configure_style()
        self._build_layout()
        self.after(0, self._startup)

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f4f7fb")
        style.configure("Panel.TFrame", background="#ffffff")
        style.configure("TLabel", background="#f4f7fb", foreground="#14213d")
        style.configure("Panel.TLabel", background="#ffffff", foreground="#14213d")
        style.configure("Muted.TLabel", foreground="#5d6b82")
        style.configure(
            "Title.TLabel",
            font=("Segoe UI", 20, "bold"),
            foreground="#102a43",
        )
        style.configure(
            "Subtitle.TLabel",
            font=("Segoe UI", 10),
            foreground="#52616f",
        )
        style.configure("TButton", font=("Segoe UI", 10), padding=(12, 8))
        style.configure(
            "Accent.TButton",
            background="#2f80ed",
            foreground="#ffffff",
            bordercolor="#2f80ed",
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#1d6fd6"), ("disabled", "#9cbce5")],
        )
        style.configure(
            "Treeview",
            rowheight=32,
            font=("Segoe UI", 10),
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground="#17212b",
        )
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _build_layout(self) -> None:
        root = ttk.Frame(self, padding=22)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=1)

        header = ttk.Frame(root)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="Windows Folder Locker", style="Title.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
        )
        ttk.Label(
            header,
            text="Protect folders with a password and Windows hidden attributes.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        toolbar = ttk.Frame(root)
        toolbar.grid(row=1, column=0, sticky="ew", pady=(18, 12))
        toolbar.columnconfigure(7, weight=1)

        ttk.Button(
            toolbar,
            text="Add Folder",
            style="Accent.TButton",
            command=self.add_folder,
        ).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(toolbar, text="Lock", command=self.lock_selected).grid(
            row=0,
            column=1,
            padx=4,
        )
        ttk.Button(toolbar, text="Unlock", command=self.unlock_selected).grid(
            row=0,
            column=2,
            padx=4,
        )
        ttk.Button(
            toolbar,
            text="Change Password",
            command=self.change_password,
        ).grid(row=0, column=3, padx=4)
        ttk.Button(toolbar, text="Forget", command=self.forget_selected).grid(
            row=0,
            column=4,
            padx=4,
        )
        ttk.Button(toolbar, text="Open", command=self.open_selected).grid(
            row=0,
            column=5,
            padx=4,
        )
        ttk.Button(toolbar, text="Refresh", command=self.refresh).grid(
            row=0,
            column=6,
            padx=4,
        )

        panel = ttk.Frame(root, style="Panel.TFrame", padding=1)
        panel.grid(row=2, column=0, sticky="nsew")
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(0, weight=1)

        columns = ("status", "path")
        self.tree = ttk.Treeview(
            panel,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("status", text="Status")
        self.tree.heading("path", text="Folder")
        self.tree.column("status", width=130, minwidth=110, anchor="center")
        self.tree.column("path", width=680, minwidth=320, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<Double-1>", lambda _event: self.unlock_selected())

        scrollbar = ttk.Scrollbar(panel, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        footer = ttk.Frame(root)
        footer.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(footer, textvariable=self.status_var, style="Muted.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
        )

    def _start_service(self) -> None:
        try:
            self.locker = create_locker(self.data_dir)
        except LockerError as exc:
            messagebox.showerror("Startup error", str(exc), parent=self)
            self.status_var.set(str(exc))

    def _startup(self) -> None:
        if not self._authenticate_app():
            self.destroy()
            return

        self._start_service()
        self.refresh()

    def _authenticate_app(self) -> bool:
        if not self.authenticator.is_configured():
            return self._create_app_password()
        return self._verify_app_password()

    def _create_app_password(self) -> bool:
        while True:
            dialog = PasswordDialog(
                self,
                "Create App Password",
                "Create the password required to open this app.",
                confirm=True,
            )
            self.wait_window(dialog)
            if dialog.result is None:
                return False

            password, _confirmation = dialog.result
            try:
                self.authenticator.set_password(password)
                self.status_var.set("App password created.")
                return True
            except LockerError as exc:
                self._show_error(exc)

    def _verify_app_password(self) -> bool:
        while True:
            dialog = PasswordDialog(
                self,
                "App Password",
                "Enter the app password to continue.",
            )
            self.wait_window(dialog)
            if not isinstance(dialog.result, str):
                return False

            try:
                self.authenticator.verify(dialog.result)
                self.status_var.set("Ready")
                return True
            except LockerError as exc:
                self._show_error(exc)

    def refresh(self) -> None:
        if self.locker is None:
            return

        for item in self.tree.get_children():
            self.tree.delete(item)
        self.folder_ids.clear()

        try:
            folders = self.locker.list_folders()
        except LockerError as exc:
            self._show_error(exc)
            return

        for folder in folders:
            item_id = self.tree.insert("", "end", values=(folder.status, str(folder.path)))
            self.folder_ids[item_id] = folder.folder_id

        self.status_var.set(f"{len(folders)} protected folder(s)")

    def add_folder(self) -> None:
        if self.locker is None:
            return

        selected = filedialog.askdirectory(title="Choose a folder to protect")
        if not selected:
            return

        dialog = PasswordDialog(
            self,
            "Create Password",
            "Create a password for this folder. Minimum length is 8 characters.",
            confirm=True,
        )
        self.wait_window(dialog)
        if dialog.result is None:
            return

        password, _confirmation = dialog.result
        try:
            self.locker.create(Path(selected), password)
            self.status_var.set("Protected folder added.")
            self.refresh()
        except LockerError as exc:
            self._show_error(exc)

    def lock_selected(self) -> None:
        folder_id = self._selected_folder_id()
        if folder_id is None or self.locker is None:
            return

        try:
            self.locker.lock(folder_id)
            self.status_var.set("Folder locked.")
            self.refresh()
        except LockerError as exc:
            self._show_error(exc)

    def unlock_selected(self) -> None:
        folder_id = self._selected_folder_id()
        if folder_id is None or self.locker is None:
            return

        dialog = PasswordDialog(self, "Unlock Folder", "Enter the folder password.")
        self.wait_window(dialog)
        if not isinstance(dialog.result, str):
            return

        try:
            self.locker.unlock(folder_id, dialog.result)
            self.status_var.set("Folder unlocked.")
            self.refresh()
        except LockerError as exc:
            self._show_error(exc)

    def change_password(self) -> None:
        folder_id = self._selected_folder_id()
        if folder_id is None or self.locker is None:
            return

        dialog = ChangePasswordDialog(self)
        self.wait_window(dialog)
        if dialog.result is None:
            return

        current_password, new_password = dialog.result
        try:
            self.locker.change_password(folder_id, current_password, new_password)
            self.status_var.set("Password changed.")
        except LockerError as exc:
            self._show_error(exc)

    def forget_selected(self) -> None:
        folder_id = self._selected_folder_id()
        if folder_id is None or self.locker is None:
            return

        confirmed = messagebox.askyesno(
            "Forget folder",
            "Remove this folder from the app? This does not delete the folder.",
            parent=self,
        )
        if not confirmed:
            return

        dialog = PasswordDialog(
            self,
            "Confirm Password",
            "Enter the password before forgetting this folder.",
        )
        self.wait_window(dialog)
        if not isinstance(dialog.result, str):
            return

        try:
            self.locker.forget(folder_id, dialog.result)
            self.status_var.set("Folder forgotten.")
            self.refresh()
        except LockerError as exc:
            self._show_error(exc)

    def open_selected(self) -> None:
        folder_id = self._selected_folder_id()
        if folder_id is None or self.locker is None:
            return

        dialog = PasswordDialog(self, "Open Folder", "Enter the folder password.")
        self.wait_window(dialog)
        if not isinstance(dialog.result, str):
            return

        try:
            self.locker.verify_password(folder_id, dialog.result, "open")
            folder = self.locker.get_folder(folder_id)
            try:
                self.locker.unlock(folder_id, dialog.result)
            except FolderStateError:
                pass
            if not folder.path.exists():
                raise FolderNotFoundError("Folder does not exist.")
            self.refresh()
            subprocess.Popen(["explorer", str(folder.path)])
            self.status_var.set("Folder opened.")
        except LockerError as exc:
            self._show_error(exc)

    def _selected_folder_id(self) -> str | None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo(
                "Select a folder",
                "Choose a protected folder first.",
                parent=self,
            )
            return None
        return self.folder_ids[selection[0]]

    def _show_error(self, exc: LockerError) -> None:
        self.status_var.set(str(exc))
        messagebox.showerror("Folder Locker", str(exc), parent=self)


def run_gui(data_dir: Path) -> int:
    """Start the desktop GUI."""

    app = FolderLockerApp(data_dir.expanduser().resolve())
    app.mainloop()
    return 0
