# Hacer Commit de Cambios

Realiza un commit de los cambios actuales siguiendo las convenciones del proyecto.

## Instrucciones

1. Ejecuta `git status` para ver los archivos modificados
2. Ejecuta `git diff` para ver los cambios
3. Ejecuta `git log --oneline -3` para ver el estilo de commits recientes
4. NO incluyas archivos de configuración local como `.claude/settings.local.json`
5. Crea un mensaje de commit descriptivo en español que explique:
   - Qué se cambió (resumen en la primera línea)
   - Por qué se cambió (detalles en el cuerpo si es necesario)
6. Usa el formato HEREDOC para el mensaje
7. Incluye el footer con el emoji de robot y Co-Authored-By
8. Ejecuta `git push` después del commit

## Formato del commit

```bash
git commit -m "$(cat <<'EOF'
Descripción corta de los cambios

- Detalle 1
- Detalle 2

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```
