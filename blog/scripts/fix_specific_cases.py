# scripts/fix_specific_cases.py
import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def fix_template_tags():
    """Corrige específicamente los template tags de comentarios"""
    tags_file = BASE_DIR / 'apps' / 'comments' / 'templatetags' / 'comments_tags.py'
    
    if not tags_file.exists():
        print(f"✗ No se encontró: {tags_file}")
        return
    
    with open(tags_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Reemplazos específicos para template tags
    replacements = [
        (r'Comentario\.objects\.filter\(aprobado=True\)', 
         "Comentario.objects.filter(estado='aprobado')"),
         
        (r'\.filter\(aprobado=True\)', 
         ".filter(estado='aprobado')"),
         
        (r'\.filter\(aprobado=False\)', 
         ".filter(estado='pendiente')"),
         
        (r'if comentario\.aprobado:', 
         "if comentario.estado == 'aprobado':"),
         
        (r'if not comentario\.aprobado:', 
         "if comentario.estado != 'aprobado':"),
    ]
    
    original_content = content
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        with open(tags_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Template tags corregidos: {tags_file}")
    else:
        print(f"✓ Template tags ya estaban correctos")

def fix_views():
    """Corrige específicamente las views"""
    views_files = [
        BASE_DIR / 'apps' / 'comments' / 'views.py',
        BASE_DIR / 'apps' / 'posts' / 'views.py',
    ]
    
    for views_file in views_files:
        if not views_file.exists():
            print(f"✗ No se encontró: {views_file}")
            continue
        
        with open(views_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Reemplazos para views
        replacements = [
            (r'\.filter\(aprobado=True\)', 
             ".filter(estado='aprobado')"),
             
            (r'\.exclude\(aprobado=True\)', 
             ".exclude(estado='aprobado')"),
             
            (r'comentario\.aprobado\s*=', 
             "comentario.estado ="),
             
            (r'if hasattr\(comentario, [\'"]aprobado[\'"]\):', 
             "if hasattr(comentario, 'estado'):"),
             
            (r'comentario\.aprobado\s*==\s*True', 
             "comentario.estado == 'aprobado'"),
             
            (r'comentario\.aprobado\s*==\s*False', 
             "comentario.estado != 'aprobado'"),
        ]
        
        original_content = content
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            with open(views_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Views corregidas: {views_file}")
        else:
            print(f"✓ Views ya estaban correctas: {views_file}")

def fix_models():
    """Agrega propiedad @property aprobado para compatibilidad si es necesario"""
    models_file = BASE_DIR / 'apps' / 'comments' / 'models.py'
    
    if not models_file.exists():
        print(f"✗ No se encontró: {models_file}")
        return
    
    with open(models_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar si ya existe la propiedad
    if '@property\s+def aprobado' in content:
        print(f"✓ La propiedad @property aprobado ya existe")
        return
    
    # Buscar el final de la clase para agregar la propiedad
    class_end_pattern = r'(\s+class\s+Meta:.*?\n\s+)(\S+)'
    match = re.search(class_end_pattern, content, re.DOTALL)
    
    if match:
        # Agregar la propiedad antes de 'class Meta:'
        new_content = content[:match.start(1)] + '''
    @property
    def aprobado(self):
        """Propiedad para compatibilidad con código antiguo que usa 'aprobado'"""
        return self.estado == 'aprobado'
''' + content[match.start(1):]
        
        with open(models_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✓ Propiedad @property aprobado agregada para compatibilidad")
    else:
        print(f"✗ No se pudo encontrar dónde agregar la propiedad")

def check_remaining_aprobado():
    """Busca referencias restantes a 'aprobado'"""
    print(f"\n{'='*60}")
    print("BUSCANDO REFERENCIAS RESTANTES A 'aprobado':")
    print(f"{'='*60}")
    
    search_dirs = [
        BASE_DIR / 'templates',
        BASE_DIR / 'apps',
    ]
    
    for search_dir in search_dirs:
        for root, dirs, files in os.walk(search_dir):
            for file in files:
                if file.endswith(('.html', '.py')):
                    file_path = os.path.join(root, file)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Buscar 'aprobado' (case insensitive)
                        if re.search(r'aprobado', content, re.IGNORECASE):
                            # Contar ocurrencias
                            count = len(re.findall(r'aprobado', content, re.IGNORECASE))
                            print(f"   {file_path}: {count} ocurrencias")
                            
                            # Mostrar líneas con contexto
                            lines = content.split('\n')
                            for i, line in enumerate(lines, 1):
                                if re.search(r'aprobado', line, re.IGNORECASE):
                                    print(f"      Línea {i}: {line.strip()[:100]}")
                    
                    except Exception as e:
                        print(f"      Error leyendo {file_path}: {e}")

def main():
    """Función principal del script específico"""
    print(f"{'='*60}")
    print("CORRECCIÓN ESPECÍFICA DE 'aprobado'")
    print(f"{'='*60}")
    
    print("\n1. Corrigiendo template tags...")
    fix_template_tags()
    
    print("\n2. Corrigiendo views...")
    fix_views()
    
    print("\n3. Agregando propiedad para compatibilidad...")
    fix_models()
    
    print("\n4. Buscando referencias restantes...")
    check_remaining_aprobado()
    
    print(f"\n{'='*60}")
    print("¡PROCESO COMPLETADO!")
    print("Recomendaciones:")
    print("1. Ejecuta 'python manage.py makemigrations' si cambiaste models.py")
    print("2. Ejecuta 'python manage.py migrate'")
    print("3. Prueba tu aplicación completamente")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()