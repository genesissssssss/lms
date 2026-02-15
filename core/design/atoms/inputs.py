"""
Atomic input components
"""
def text_input(name, placeholder="", value="", required=False, classes=""):
    """Text input atom"""
    base_classes = "w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
    required_attr = "required" if required else ""
    return f'''
    <input type="text" 
           name="{name}" 
           placeholder="{placeholder}" 
           value="{value}" 
           {required_attr}
           class="{base_classes} {classes}">
    '''

def email_input(name, placeholder="", value="", required=False, classes=""):
    """Email input atom"""
    base_classes = "w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
    required_attr = "required" if required else ""
    return f'''
    <input type="email" 
           name="{name}" 
           placeholder="{placeholder}" 
           value="{value}" 
           {required_attr}
           class="{base_classes} {classes}">
    '''

def password_input(name, placeholder="", required=False, classes=""):
    """Password input atom"""
    base_classes = "w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
    required_attr = "required" if required else ""
    return f'''
    <input type="password" 
           name="{name}" 
           placeholder="{placeholder}" 
           {required_attr}
           class="{base_classes} {classes}">
    '''