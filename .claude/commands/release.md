# Crear Release en GitHub

Crea un nuevo release en GitHub usando `gh`.

## Instrucciones

1. Ejecuta `gh release list --limit 3` para ver los releases anteriores
2. Determina la nueva versión siguiendo semver (vX.Y.Z):
   - Patch (X.Y.Z+1): Corrección de bugs, correcciones menores
   - Minor (X.Y+1.0): Nuevas funcionalidades backwards-compatible
   - Major (X+1.0.0): Cambios que rompen compatibilidad (breaking changes)
3. Ejecuta `git log --oneline <ultimo_tag>..HEAD` para ver los commits desde el último release
4. Crea el release con notas descriptivas

## Formato del release

```bash
gh release create vX.Y.Z --title "vX.Y.Z - Descripción corta" --notes "$(cat <<'EOF'
## Cambios

### Funcionalidades
- Funcionalidad 1
- Funcionalidad 2

### Correcciones de Bugs
- Corrección 1
- Corrección 2

### Técnico
- Cambio técnico 1

## Despliegue

Instrucciones si es necesario...
EOF
)"
```

## Ejemplo

```bash
gh release create v1.0.3 --title "v1.0.3 - Refactorización de gestión de negocios" --notes "$(cat <<'EOF'
## Cambios

### Refactorización
- Refactorizada la gestión de negocios para seguir las guías CRUD
- Corregido problema del loader en modal de configuración de negocio

## Despliegue

Pull y rebuild en servidor:
\`\`\`bash
docker compose build --no-cache && docker compose down && docker compose up -d
\`\`\`
EOF
)"
```
