# Commit y Release

Combina commit y release en un solo flujo.

## Instrucciones

1. Primero ejecuta el flujo de `/commit`:
   - `git status` y `git diff` para revisar cambios
   - Crear commit con mensaje descriptivo
   - `git push`

2. Luego ejecuta el flujo de `/release`:
   - `gh release list --limit 3` para ver versión anterior
   - Incrementar versión según los cambios
   - Crear release con notas

## Flujo completo

```bash
# 1. Ver cambios
git status
git diff --stat

# 2. Commit (sin archivos locales)
git add <archivos>
git commit -m "$(cat <<'EOF'
Descripción

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# 3. Push
git push

# 4. Ver último release
gh release list --limit 1

# 5. Crear release
gh release create vX.Y.Z --title "vX.Y.Z - Título" --notes "..."
```

## Salida esperada

Al finalizar, mostrar:
- URL del commit en GitHub
- URL del release creado
- Comandos para deploy en servidor si aplica
