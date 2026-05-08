from settings import BACKEND_URL

class URLs:
    class Backend:
        login =                 f"{BACKEND_URL}/login/"
        logout =                f"{BACKEND_URL}/logoff/"
        issues =                f"{BACKEND_URL}/issues/"
        print_types =           f"{BACKEND_URL}/print_types/"
        signup =                f"{BACKEND_URL}/users/"
        stamps =                f"{BACKEND_URL}/stamps/"
        stamp_types =           f"{BACKEND_URL}/stamps_type/"
        years =                 f"{BACKEND_URL}/years/"
        config =                f"{BACKEND_URL}/config/"
        issues_extraction =     f"{BACKEND_URL}/issues/extraction/"
        issues_collections =    f"{BACKEND_URL}/issues/collections/"
        
    class Frontend:
        collections =           "/collections"
        login =                 "/login"
        logout =                "/logout"
        root =                  "/"
        signup =                "/signup"
        stamps_manager =        "/admin/stamps/manager"