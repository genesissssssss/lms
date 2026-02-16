"""
Atomic button components for the LMS
"""
def primary_button(text, href=None, type="button", classes=""):
    """Primary button atom"""
    base_classes = "bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-lg transition duration-200"
    if href:
        return f'<a href="{href}" class="{base_classes} {classes}">{text}</a>'
    return f'<button type="{type}" class="{base_classes} {classes}">{text}</button>'

def secondary_button(text, href=None, type="button", classes=""):
    """Secondary button atom"""
    base_classes = "border border-gray-600 hover:border-primary-400 text-gray-300 hover:text-white font-medium py-2 px-4 rounded-lg transition duration-200"
    if href:
        return f'<a href="{href}" class="{base_classes} {classes}">{text}</a>'
    return f'<button type="{type}" class="{base_classes} {classes}">{text}</button>'

def icon_button(icon_name, href=None, classes=""):
    """Icon button atom"""
    base_classes = "p-2 hover:bg-gray-800 rounded-lg transition"
    icon = f'<span class="material-icons">{icon_name}</span>'
    if href:
        return f'<a href="{href}" class="{base_classes} {classes}">{icon}</a>'
    return f'<button class="{base_classes} {classes}">{icon}</button>'