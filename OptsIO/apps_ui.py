from OptsIO.models import Menu as MenuModel, Apps, AppsBookMakrs, UserProfile, RolesUser, RolesApps


class Menu:
    """Clase para manejar la lógica de menús y apps"""

    def __init__(self):
        pass

    def get_apps(self, *args, **kwargs):
        """
        Obtiene las apps activas filtradas por roles del usuario.
        - Si el usuario es superuser: retorna todas las apps
        - Si el usuario tiene roles: retorna solo las apps asignadas a sus roles
        - Si el usuario no tiene roles: retorna lista vacía
        """
        userobj = kwargs.get('userobj')

        # Obtener prioridades de los menús
        menu_priorities = {
            m.menu: m.prioridad
            for m in MenuModel.objects.filter(active=True)
        }

        # Si el usuario es superuser, retornar todas las apps
        if userobj and userobj.is_superuser:
            apps = Apps.objects.filter(active=True).values(
                'id',
                'prioridad',
                'menu',
                'menu_icon',
                'app_name',
                'friendly_name',
                'icon',
                'url',
                'version',
                'background',
                'active'
            )
        elif userobj:
            # Obtener UserProfile del usuario
            try:
                user_profile = UserProfile.objects.get(username=userobj.username)

                # Obtener roles activos del usuario
                user_roles = RolesUser.objects.filter(
                    userprofileobj=user_profile,
                    active=True
                ).values_list('rolesobj_id', flat=True)

                if user_roles:
                    # Obtener apps asignadas a los roles del usuario
                    allowed_app_ids = RolesApps.objects.filter(
                        rolesobj_id__in=user_roles,
                        active=True
                    ).values_list('appsobj_id', flat=True).distinct()

                    # Filtrar apps por las permitidas
                    apps = Apps.objects.filter(
                        id__in=allowed_app_ids,
                        active=True
                    ).values(
                        'id',
                        'prioridad',
                        'menu',
                        'menu_icon',
                        'app_name',
                        'friendly_name',
                        'icon',
                        'url',
                        'version',
                        'background',
                        'active'
                    )
                else:
                    # Usuario sin roles: retornar lista vacía
                    apps = Apps.objects.none().values()

            except UserProfile.DoesNotExist:
                # Usuario sin perfil: retornar lista vacía
                apps = Apps.objects.none().values()
        else:
            # Sin usuario: retornar lista vacía
            apps = Apps.objects.none().values()

        # Agregar prioridad del menú y ordenar
        apps_list = list(apps)
        for app in apps_list:
            app['menu_prioridad'] = menu_priorities.get(app['menu'], 999)

        # Ordenar por prioridad del menú, luego por prioridad de la app
        apps_list.sort(key=lambda x: (x['menu_prioridad'], x['prioridad']))

        return apps_list

    def get_menus(self, *args, **kwargs):
        """
        Obtiene todos los menús activos
        """
        menus = MenuModel.objects.filter(active=True).order_by('prioridad').values(
            'id',
            'prioridad',
            'menu',
            'friendly_name',
            'icon',
            'url',
            'background',
            'active'
        )

        return list(menus)

    def get_bookmarks(self, *args, **kwargs):
        """
        Obtiene los bookmarks del usuario actual
        """
        userobj = kwargs.get('userobj')
        if not userobj:
            return []

        username = userobj.username

        bookmarks = AppsBookMakrs.objects.filter(
            username=username
        ).select_related('app').order_by('prioridad')

        result = []
        for bookmark in bookmarks:
            if bookmark.app.active:
                result.append({
                    'id': bookmark.id,
                    'prioridad': bookmark.prioridad,
                    'app': {
                        'id': bookmark.app.id,
                        'app_name': bookmark.app.app_name,
                        'friendly_name': bookmark.app.friendly_name,
                        'icon': bookmark.app.icon,
                        'url': bookmark.app.url,
                        'background': bookmark.app.background
                    }
                })

        return result

    def add_bookmark(self, *args, **kwargs):
        """
        Agrega una app a los bookmarks del usuario
        """
        userobj = kwargs.get('userobj')
        if not userobj:
            return {'success': False, 'message': 'Usuario no autenticado'}

        q = kwargs.get('qdict', {})
        app_id = q.get('app_id')
        username = userobj.username

        try:
            app = Apps.objects.get(id=app_id)

            # Verificar si ya existe
            existing = AppsBookMakrs.objects.filter(
                app=app,
                username=username
            ).first()

            if existing:
                return {'success': False, 'message': 'Ya existe en favoritos'}

            # Obtener la última prioridad
            last_priority = AppsBookMakrs.objects.filter(
                username=username
            ).order_by('-prioridad').first()

            priority = (last_priority.prioridad + 1) if last_priority else 1

            bookmark = AppsBookMakrs.objects.create(
                app=app,
                username=username,
                prioridad=priority
            )

            return {
                'success': True,
                'message': 'Agregado a favoritos',
                'bookmark': {
                    'id': bookmark.id,
                    'prioridad': bookmark.prioridad
                }
            }

        except Apps.DoesNotExist:
            return {'success': False, 'message': 'App no encontrada'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def remove_bookmark(self, *args, **kwargs):
        """
        Elimina una app de los bookmarks del usuario
        """
        userobj = kwargs.get('userobj')
        if not userobj:
            return {'success': False, 'message': 'Usuario no autenticado'}

        q = kwargs.get('qdict', {})
        bookmark_id = q.get('bookmark_id')
        username = userobj.username

        try:
            bookmark = AppsBookMakrs.objects.get(
                id=bookmark_id,
                username=username
            )
            bookmark.delete()

            return {'success': True, 'message': 'Eliminado de favoritos'}

        except AppsBookMakrs.DoesNotExist:
            return {'success': False, 'message': 'Bookmark no encontrado'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def update_bookmark_order(self, *args, **kwargs):
        """
        Actualiza el orden de los bookmarks del usuario (drag & drop)
        Recibe una lista de bookmark_ids en el nuevo orden
        """
        userobj = kwargs.get('userobj')
        if not userobj:
            return {'success': False, 'message': 'Usuario no autenticado'}

        q = kwargs.get('qdict', {})
        bookmark_ids = q.get('bookmark_ids', [])
        username = userobj.username

        if isinstance(bookmark_ids, str):
            import json
            try:
                bookmark_ids = json.loads(bookmark_ids)
            except:
                bookmark_ids = []

        try:
            for index, bookmark_id in enumerate(bookmark_ids):
                AppsBookMakrs.objects.filter(
                    id=bookmark_id,
                    username=username
                ).update(prioridad=index)

            return {'success': True, 'message': 'Orden actualizado'}

        except Exception as e:
            return {'success': False, 'message': str(e)}
