Menu.objects.create(
    prioridad = 5,
    menu = 'Test',
    friendly_name = 'Test',
    icon = 'mdi mdi-ocr',
    url = '#',
    background = '#0AAA20FF',
    active = True
)

Apps.objects.create(
    prioridad= 1,
    menu= 'Anime',
    app_name= 'anime_list',
    friendly_name= 'Anime',
    icon= 'mdi mdi-animation',
    url= 'Anime/AnimeUi.html',
    version= '1.0',
    background= '#F6A65CFF',
    active= True
)


