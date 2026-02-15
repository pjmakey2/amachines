from django.core.management.base import BaseCommand
from OptsIO.models import Menu, Apps


class Command(BaseCommand):
    help = 'Crea las entradas de menú y apps del sistema'

    def handle(self, *args, **options):
        # Definir menús
        menus_data = [
            {
                'menu': 'Transacciones',
                'prioridad': 10,
                'friendly_name': 'Transacciones',
                'icon': 'mdi mdi-file-document-edit',
                'background': '#4F46E5',
            },
            {
                'menu': 'Timbrado',
                'prioridad': 15,
                'friendly_name': 'Timbrado',
                'icon': 'mdi mdi-stamper',
                'background': '#7C3AED',
            },
            {
                'menu': 'Negocio',
                'prioridad': 20,
                'friendly_name': 'Negocio',
                'icon': 'mdi mdi-domain',
                'background': '#059669',
            },
            {
                'menu': 'Maestros',
                'prioridad': 25,
                'friendly_name': 'Datos Maestros',
                'icon': 'mdi mdi-database',
                'background': '#10B981',
            },
            {
                'menu': 'Geografías',
                'prioridad': 30,
                'friendly_name': 'Geografías',
                'icon': 'mdi mdi-map-marker',
                'background': '#F59E0B',
            },
            {
                'menu': 'Sistema',
                'prioridad': 40,
                'friendly_name': 'Sistema',
                'icon': 'mdi mdi-cog',
                'background': '#6B7280',
            },
            {
                'menu': 'Apps',
                'prioridad': 50,
                'friendly_name': 'Administración',
                'icon': 'mdi mdi-apps',
                'background': '#3B82F6',
            },
        ]

        # Crear menús
        for menu_data in menus_data:
            menu, created = Menu.objects.update_or_create(
                menu=menu_data['menu'],
                defaults={
                    'prioridad': menu_data['prioridad'],
                    'friendly_name': menu_data['friendly_name'],
                    'icon': menu_data['icon'],
                    'url': '#',
                    'background': menu_data['background'],
                    'active': True
                }
            )
            status = 'creado' if created else 'actualizado'
            self.stdout.write(self.style.SUCCESS(f'Menú "{menu_data["menu"]}" {status}'))

        # Definir apps por menú
        apps_data = [
            # === TRANSACCIONES ===
            {
                'prioridad': 1,
                'menu': 'Transacciones',
                'app_name': 'sifen_facturar',
                'friendly_name': 'Facturar',
                'icon': 'mdi mdi-file-document-edit',
                'url': 'Sifen/DocumentHeaderUi.html',
                'background': '#4F46E5',
            },
            {
                'prioridad': 2,
                'menu': 'Transacciones',
                'app_name': 'sifen_documentnc',
                'friendly_name': 'Notas de Crédito',
                'icon': 'mdi mdi-file-document-minus',
                'url': 'Sifen/DocumentNcUi.html',
                'background': '#7C3AED',
            },
            {
                'prioridad': 3,
                'menu': 'Transacciones',
                'app_name': 'sifen_retenciones',
                'friendly_name': 'Retenciones',
                'icon': 'mdi mdi-file-percent',
                'url': 'Sifen/RetencionHomeUi.html',
                'background': '#8B5CF6',
            },
            {
                'prioridad': 4,
                'menu': 'Transacciones',
                'app_name': 'sifen_recibo',
                'friendly_name': 'Recibo',
                'icon': 'mdi mdi-file-check',
                'url': 'Sifen/DocumentReciboHomeUi.html',
                'background': '#A78BFA',
            },

            # === TIMBRADO ===
            {
                'prioridad': 1,
                'menu': 'Timbrado',
                'app_name': 'Etimbrado',
                'friendly_name': 'Timbrados',
                'icon': 'mdi mdi-stamper',
                'url': 'Sifen/EtimbradoUi.html',
                'background': '#7C3AED',
            },
            {
                'prioridad': 2,
                'menu': 'Timbrado',
                'app_name': 'EnumberCreate',
                'friendly_name': 'Crear Timbrado',
                'icon': 'mdi mdi-plus-circle',
                'url': 'Sifen/EnumberCreateUi.html',
                'background': '#8B5CF6',
            },
            {
                'prioridad': 3,
                'menu': 'Timbrado',
                'app_name': 'Eestablecimiento',
                'friendly_name': 'Establecimientos',
                'icon': 'mdi mdi-store',
                'url': 'Sifen/EestablecimientoUi.html',
                'background': '#A78BFA',
            },
            {
                'prioridad': 4,
                'menu': 'Timbrado',
                'app_name': 'EnumberExtend',
                'friendly_name': 'Gestion Numeros',
                'icon': 'mdi mdi-cog-outline',
                'url': 'Sifen/EnumberExtendUi.html',
                'background': '#C4B5FD',
            },
            {
                'prioridad': 5,
                'menu': 'Timbrado',
                'app_name': 'TrackLotes',
                'friendly_name': 'Track Lotes',
                'icon': 'mdi mdi-truck-delivery',
                'url': 'Sifen/SoapMsgUi.html',
                'background': '#6366F1',
            },

            # === NEGOCIO ===
            {
                'prioridad': 1,
                'menu': 'Negocio',
                'app_name': 'Business',
                'friendly_name': 'Empresas',
                'icon': 'mdi mdi-domain',
                'url': 'Sifen/BusinessUi.html',
                'background': '#059669',
            },
            {
                'prioridad': 2,
                'menu': 'Negocio',
                'app_name': 'Certificate',
                'friendly_name': 'Certificados Digitales',
                'icon': 'mdi mdi-file-key',
                'url': 'Sifen/CertificateHomeUi.html',
                'background': '#10B981',
            },
            {
                'prioridad': 3,
                'menu': 'Negocio',
                'app_name': 'ActividadEconomica',
                'friendly_name': 'Actividades Económicas',
                'icon': 'mdi mdi-briefcase',
                'url': 'Sifen/ActividadEconomicaUi.html',
                'background': '#047857',
            },
            {
                'prioridad': 4,
                'menu': 'Negocio',
                'app_name': 'BusinessUser',
                'friendly_name': 'Usuarios de Negocio',
                'icon': 'mdi mdi-account-network',
                'url': 'OptsIO/BusinessUserUi.html',
                'background': '#0D9488',
            },

            # === MAESTROS ===
            {
                'prioridad': 1,
                'menu': 'Maestros',
                'app_name': 'PorcentajeIva',
                'friendly_name': 'Porcentajes IVA',
                'icon': 'mdi mdi-percent',
                'url': 'Sifen/PorcentajeIvaUi.html',
                'background': '#10B981',
            },
            {
                'prioridad': 2,
                'menu': 'Maestros',
                'app_name': 'Producto',
                'friendly_name': 'Productos',
                'icon': 'mdi mdi-package-variant',
                'url': 'Sifen/ProductoUi.html',
                'background': '#059669',
            },
            {
                'prioridad': 3,
                'menu': 'Maestros',
                'app_name': 'Categoria',
                'friendly_name': 'Categorías',
                'icon': 'mdi mdi-shape',
                'url': 'Sifen/CategoriaUi.html',
                'background': '#047857',
            },
            {
                'prioridad': 4,
                'menu': 'Maestros',
                'app_name': 'Marca',
                'friendly_name': 'Marcas',
                'icon': 'mdi mdi-tag',
                'url': 'Sifen/MarcaUi.html',
                'background': '#065F46',
            },
            {
                'prioridad': 5,
                'menu': 'Maestros',
                'app_name': 'TipoContribuyente',
                'friendly_name': 'Tipos de Contribuyente',
                'icon': 'mdi mdi-account-group',
                'url': 'Sifen/TipoContribuyenteUi.html',
                'background': '#10B981',
            },
            {
                'prioridad': 6,
                'menu': 'Maestros',
                'app_name': 'Clientes',
                'friendly_name': 'Clientes',
                'icon': 'mdi mdi-account-multiple',
                'url': 'Sifen/ClienteUi.html',
                'background': '#047857',
            },

            # === GEOGRAFÍAS ===
            {
                'prioridad': 1,
                'menu': 'Geografías',
                'app_name': 'Barrios',
                'friendly_name': 'Barrios',
                'icon': 'mdi mdi-home-group',
                'url': 'Sifen/BarriosUi.html',
                'background': '#F59E0B',
            },
            {
                'prioridad': 2,
                'menu': 'Geografías',
                'app_name': 'Geografias',
                'friendly_name': 'Geografías',
                'icon': 'mdi mdi-earth',
                'url': 'Sifen/GeografiasUi.html',
                'background': '#D97706',
            },
            {
                'prioridad': 3,
                'menu': 'Geografías',
                'app_name': 'AreasPoliticas',
                'friendly_name': 'Áreas Políticas',
                'icon': 'mdi mdi-map',
                'url': 'Sifen/AreasPoliticasUi.html',
                'background': '#B45309',
            },
            {
                'prioridad': 4,
                'menu': 'Geografías',
                'app_name': 'Paises',
                'friendly_name': 'Países',
                'icon': 'mdi mdi-flag',
                'url': 'Sifen/PaisesUi.html',
                'background': '#92400E',
            },
            {
                'prioridad': 5,
                'menu': 'Geografías',
                'app_name': 'Departamentos',
                'friendly_name': 'Departamentos',
                'icon': 'mdi mdi-map-marker-radius',
                'url': 'Sifen/DepartamentosUi.html',
                'background': '#78350F',
            },
            {
                'prioridad': 6,
                'menu': 'Geografías',
                'app_name': 'Distrito',
                'friendly_name': 'Distritos',
                'icon': 'mdi mdi-map-marker-outline',
                'url': 'Sifen/DistritoUi.html',
                'background': '#F59E0B',
            },
            {
                'prioridad': 7,
                'menu': 'Geografías',
                'app_name': 'Ciudades',
                'friendly_name': 'Ciudades',
                'icon': 'mdi mdi-city',
                'url': 'Sifen/CiudadesUi.html',
                'background': '#D97706',
            },

            # === SISTEMA ===
            {
                'prioridad': 1,
                'menu': 'Sistema',
                'app_name': 'UserProfile',
                'friendly_name': 'Mi Perfil',
                'icon': 'mdi mdi-account-circle',
                'url': 'OptsIO/UserProfileUi.html',
                'background': '#6B7280',
            },
            {
                'prioridad': 2,
                'menu': 'Sistema',
                'app_name': 'Roles',
                'friendly_name': 'Roles',
                'icon': 'mdi mdi-shield-account',
                'url': 'OptsIO/RolesUi.html',
                'background': '#4B5563',
            },
            {
                'prioridad': 3,
                'menu': 'Sistema',
                'app_name': 'RolesUser',
                'friendly_name': 'Roles de Usuarios',
                'icon': 'mdi mdi-account-key',
                'url': 'OptsIO/RolesUserUi.html',
                'background': '#374151',
            },
            {
                'prioridad': 4,
                'menu': 'Sistema',
                'app_name': 'RolesApps',
                'friendly_name': 'Permisos de Aplicaciones',
                'icon': 'mdi mdi-application-cog',
                'url': 'OptsIO/RolesAppsUi.html',
                'background': '#1F2937',
            },
            {
                'prioridad': 5,
                'menu': 'Sistema',
                'app_name': 'User',
                'friendly_name': 'Usuarios',
                'icon': 'mdi mdi-account-multiple',
                'url': 'OptsIO/UserUi.html',
                'background': '#111827',
            },

            # === APPS ===
            {
                'prioridad': 1,
                'menu': 'Apps',
                'app_name': 'Menu',
                'friendly_name': 'Menús',
                'icon': 'mdi mdi-menu',
                'url': 'OptsIO/MenuUi.html',
                'background': '#3B82F6',
            },
            {
                'prioridad': 2,
                'menu': 'Apps',
                'app_name': 'Apps',
                'friendly_name': 'Aplicaciones',
                'icon': 'mdi mdi-apps',
                'url': 'OptsIO/AppsUi.html',
                'background': '#2563EB',
            },
            {
                'prioridad': 3,
                'menu': 'Apps',
                'app_name': 'AppsBookMakrs',
                'friendly_name': 'Favoritos de Apps',
                'icon': 'mdi mdi-star',
                'url': 'OptsIO/AppsBookMakrsUi.html',
                'background': '#1D4ED8',
            },
        ]

        # Lista de app_names válidos (solo del core)
        valid_app_names = [app['app_name'] for app in apps_data]

        # Lista de menús core
        valid_menus = [m['menu'] for m in menus_data]

        # Solo eliminar apps que pertenecen a menús CORE y ya no están en la lista
        # Esto preserva apps de plugins externos (ej: fl_facturacion_legacy)
        deleted_count = Apps.objects.filter(
            menu__in=valid_menus
        ).exclude(
            app_name__in=valid_app_names
        ).delete()[0]
        if deleted_count > 0:
            self.stdout.write(self.style.WARNING(f'Apps core eliminadas: {deleted_count}'))

        # NO eliminar menús de plugins externos
        # Solo este comando gestiona los menús core definidos arriba

        # Crear/actualizar apps
        created_count = 0
        updated_count = 0

        for app_data in apps_data:
            app, created = Apps.objects.update_or_create(
                app_name=app_data['app_name'],
                defaults={
                    'prioridad': app_data['prioridad'],
                    'menu': app_data['menu'],
                    'friendly_name': app_data['friendly_name'],
                    'icon': app_data['icon'],
                    'url': app_data['url'],
                    'version': '1.0',
                    'background': app_data['background'],
                    'active': True
                }
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Apps creadas: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'Apps actualizadas: {updated_count}'))
        self.stdout.write(self.style.SUCCESS(f'Total apps: {len(apps_data)}'))
        self.stdout.write(self.style.SUCCESS('\nConfiguración de menús y apps completada!'))
