# scripts/replace_aprobado.py
import os
import re
from pathlib import Path

# Configuración
BASE_DIR = Path(__file__).resolve().parent.parent  # Ajusta según tu estructura
TEMPLATES_DIR = BASE_DIR / 'templates'
APPS_DIR = BASE_DIR / 'apps'

# Patrones de búsqueda y reemplazo
PATTERNS = [
    # ========== PATRONES PARA TEMPLATES HTML ==========
    {
        'ext': '.html',
        'patterns': [
            # 1. Filtros directos en templates
            (r'(\{\%\s*for\s+comentario\s+in\s+)(\w+)(\.comentarios\.filter\(aprobado=True\))', 
             r'\1\2.comentarios.filter(estado=\'aprobado\')'),
             
            (r'(\{\%\s*for\s+comentario\s+in\s+)(\w+)(\.comentarios\.all\(\).*?aprobado.*?\})', 
             r'\1\2.comentarios.filter(estado=\'aprobado\')'),
            
            # 2. Condicionales
            (r'(\{\%\s*if\s+)(comentario\.aprobado)(\s*\%\})', 
             r'\1comentario.estado == \'aprobado\'\3'),
             
            (r'(\{\%\s*if\s+not\s+)(comentario\.aprobado)(\s*\%\})', 
             r'\1comentario.estado != \'aprobado\'\3'),
            
            # 3. Enlaces o botones condicionales
            (r'(\{\%\s*if\s+)(\w+\.aprobado)(\s*\%\})', 
             r'\1\2.estado == \'aprobado\'\3'),
            
            # 4. Filtros en template tags (simple)
            (r'(\{\%\s*get_recent_comments.*?\}\})', 
             lambda m: m.group(0)),  # Esto necesita revisión manual
            
            # 5. En JavaScript dentro de templates
            (r'(data-aprobado=["\'])(true|false)(["\'])', 
             r'data-estado="\2"'),
        ]
    },
    
    # ========== PATRONES PARA ARCHIVOS PYTHON ==========
    {
        'ext': '.py',
        'patterns': [
            # 1. Filtros en QuerySets
            (r'(\.filter\(aprobado=True\))', 
             r".filter(estado='aprobado')"),
             
            (r'(\.filter\(aprobado=False\))', 
             r".filter(estado='pendiente')"),
            
            # 2. Filtros con Q objects
            (r'(Q\(aprobado=True\))', 
             r"Q(estado='aprobado')"),
            
            # 3. Acceso a atributo
            (r'(\w+)\.aprobado', 
             r"\1.estado == 'aprobado'"),
            
            # 4. En condicionales
            (r'(if\s+)(\w+\.aprobado)(:)', 
             r"\1\2.estado == 'aprobado':"),
             
            (r'(if\s+not\s+)(\w+\.aprobado)(:)', 
             r"\1\2.estado != 'aprobado':"),
            
            # 5. En funciones o métodos
            (r'(def.*aprobado.*:)', 
             lambda m: m.group(0)),  # Revisar manualmente
        ]
    }
]

def process_file(file_path, patterns):
    """Procesa un archivo y aplica los reemplazos"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_made = 0
    
    for pattern, replacement in patterns:
        if callable(replacement):
            # Para reemplazos complejos que necesitan revisión manual
            continue
        
        new_content, num_subs = re.subn(pattern, replacement, content, flags=re.IGNORECASE)
        if num_subs > 0:
            content = new_content
            changes_made += num_subs
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return changes_made
    
    return 0

def find_and_replace():
    """Busca y reemplaza en todos los archivos"""
    total_changes = 0
    files_processed = 0
    
    # Procesar templates HTML
    for root, dirs, files in os.walk(TEMPLATES_DIR):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                patterns = next((p['patterns'] for p in PATTERNS if p['ext'] == '.html'), [])
                
                changes = process_file(file_path, patterns)
                if changes > 0:
                    print(f"✓ {file_path}: {changes} cambios")
                    total_changes += changes
                files_processed += 1
    
    # Procesar archivos Python
    for root, dirs, files in os.walk(APPS_DIR):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                patterns = next((p['patterns'] for p in PATTERNS if p['ext'] == '.py'), [])
                
                changes = process_file(file_path, patterns)
                if changes > 0:
                    print(f"✓ {file_path}: {changes} cambios")
                    total_changes += changes
                files_processed += 1
    
    print(f"\n{'='*60}")
    print(f"RESUMEN:")
    print(f"Archivos procesados: {files_processed}")
    print(f"Total de cambios: {total_changes}")
    print(f"{'='*60}")

def manual_review_checklist():
    """Proporciona una checklist para revisiones manuales"""
    print(f"\n{'='*60}")
    print("REVISIONES MANUALES NECESARIAS:")
    print(f"{'='*60}")
    
    checklist = [
        "1. Template tags personalizados (get_recent_comments, etc.)",
        "2. Funciones con 'aprobado' en el nombre",
        "3. Comentarios en el código que mencionen 'aprobado'",
        "4. Archivos de migraciones (no tocar)",
        "5. Archivos de configuración (settings.py, urls.py)",
        "6. Models si tienen propiedad @property aprobado",
        "7. Forms si tienen campos relacionados con 'aprobado'",
    ]
    
    for item in checklist:
        print(f"   {item}")
    
    print(f"\nARCHIVOS CRÍTICOS PARA REVISAR:")
    critical_files = [
        "apps/comments/templatetags/comments_tags.py",
        "apps/comments/models.py",
        "apps/comments/views.py",
        "apps/comments/forms.py",
        "apps/posts/views.py",
        "templates/comments/_comentarios.html",
        "templates/post/listar_posts.html",
        "templates/post/listar_por_categoria.html",
        "templates/post/ver_post.html",
    ]
    
    for file in critical_files:
        full_path = BASE_DIR / file
        if full_path.exists():
            print(f"   • {file}")
        else:
            print(f"   • {file} (no encontrado)")

def create_backup():
    """Crea un backup de los archivos modificados"""
    import shutil
    import datetime
    
    backup_dir = BASE_DIR / 'backups' / f'aprobado_fix_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}'
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Copiar templates
    shutil.copytree(TEMPLATES_DIR, backup_dir / 'templates', dirs_exist_ok=True)
    
    # Copiar apps
    shutil.copytree(APPS_DIR, backup_dir / 'apps', dirs_exist_ok=True)
    
    print(f"\n✓ Backup creado en: {backup_dir}")
    return backup_dir

def main():
    """Función principal"""
    print(f"{'='*60}")
    print("SCRIPT PARA REEMPLAZAR 'aprobado' POR 'estado=\\'aprobado\\''")
    print(f"{'='*60}")
    
    print("\nEste script buscará y reemplazará referencias a 'aprobado'")
    print("en tus templates y archivos Python.")
    
    respuesta = input("\n¿Deseas crear un backup antes de continuar? (s/n): ")
    if respuesta.lower() == 's':
        backup_path = create_backup()
        print(f"Backup guardado en: {backup_path}")
    
    print("\nProcesando archivos...")
    find_and_replace()
    
    manual_review_checklist()
    
    print(f"\n{'='*60}")
    print("¡PROCESO COMPLETADO!")
    print("Recuerda:")
    print("1. Revisar los archivos críticos manualmente")
    print("2. Probar la aplicación después de los cambios")
    print("3. Ejecutar 'python manage.py test' si tienes tests")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()