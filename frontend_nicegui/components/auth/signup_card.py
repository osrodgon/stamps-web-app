import re

from core.base_ui import BaseUI
from core.translations import _
from nicegui import ui


class SignUpCard(ui.card, BaseUI):
    def __init__(self, on_sign_up: callable = None, on_back: callable = None):
        super().__init__()
        self.log.debug("Initializating SignUpCard...")
        
        with self.classes('w-auto p-6 shadow-xl rounded-lg'):
            ui.label(_('auth.create_account')).classes('text-2xl font-bold')
            ui.label(_('auth.account_details')).classes('text-sm text-gray-500 mb-4')
            
            # Helper to trigger signup only if terms are accepted
            handle_enter = lambda: on_sign_up() if terms_checkbox.value else None

            with ui.row().classes('w-full gap-x-4'):
                self.name_input = ui.input(
                    label=_('auth.first_name'), 
                    placeholder='John', 
                    validation={_('ui.required'): lambda v: len(v) > 0}
                ).classes('w-[calc(50%-8px)]').on('keydown.enter', handle_enter)
                self.last_name_input = ui.input(
                    label=_('auth.last_name'), 
                    placeholder='Doe', 
                    validation={_('ui.required'): lambda v: len(v) > 0}
                ).classes('w-[calc(50%-8px)]').on('keydown.enter', handle_enter) 

            self.username_input = ui.input(
                label=_('auth.username'), 
                placeholder='johndoe', 
                validation={_('ui.required'): lambda v: len(v) > 0}
            ).classes('w-full').on('keydown.enter', handle_enter)
            self.email_input = ui.input(
                label=_('auth.email'), 
                placeholder='john@example.com',
                validation={
                    _('ui.required'): lambda v: len(v) > 0,
                    _('auth.invalid_email'): lambda v: bool(re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", v))
                }
            ).classes('w-full').on('keydown.enter', handle_enter) 
            
            with ui.row().classes('w-full gap-x-4'):
                self.password_input = ui.input(
                    label=_('auth.password'), 
                    placeholder='••••••••', 
                    password=True, 
                    password_toggle_button=True,
                    validation={
                        _('ui.required'): lambda v: len(v) > 0,
                        _('auth.invalid_password'): lambda v: len(v) >= 8 and 
                            re.search(r"[A-Z]", v) and 
                            re.search(r"[a-z]", v) and 
                            re.search(r"\d", v) and 
                            re.search(r"[^a-zA-Z0-9]", v)
                    }
                ).classes('w-full').on('keydown.enter', handle_enter)
                self.confirm_password_input = ui.input(
                    label=_('auth.confirm_password'), 
                    placeholder='••••••••', 
                    password=True, 
                    password_toggle_button=True,
                    validation={
                        _('ui.required'): lambda v: len(v) > 0,
                        _('auth.password_not_match'): lambda v: v == self.password_input.value
                    }
                ).classes('w-full').on('keydown.enter', handle_enter)

            checkbox_row = ui.row().classes('w-full items-center mb-4')
            with checkbox_row:
                terms_checkbox = ui.checkbox().classes('q-mt-none').props('id="terms_checkbox"')
                ui.html(_('auth.agree'), sanitize=False).classes('text-sm')

            with ui.row().classes('w-full gap-x-4'):
                submit_button = ui.button(_('auth.sign_up'), on_click=on_sign_up).classes('w-[calc(50%-8px)]')
                submit_button.bind_enabled_from(terms_checkbox, 'value')

                ui.button(_('ui.cancel'), on_click=on_back).classes('w-[calc(50%-8px)]')
            
    def is_valid(self):
        valid = all([
            self.name_input.validate(),
            self.last_name_input.validate(),
            self.username_input.validate(),
            self.email_input.validate(),
            self.password_input.validate(),
            self.confirm_password_input.validate(),
        ])
        
        self.log.debug(f"SignUp form validation result: {valid}")
        
        return valid
    
    def get_data(self):
        return {
            'first_name': self.name_input.value,
            'last_name': self.last_name_input.value,
            'username': self.username_input.value,
            'email': self.email_input.value,
            'password': self.password_input.value
        }