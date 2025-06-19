##map/map_widget.py
import os
import json
from map.map_loader import MapLoader
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QObject, pyqtSlot, QUrl
from PyQt5.QtWebChannel import QWebChannel

class MapBridge(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_coordinates = []
    @pyqtSlot(float, float)
    def add_point(self, lat, lng):
        self.current_coordinates.append([lat, lng])

class MapWidget(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.API_KEY = "718490f1-55ce-41d2-9cd3-3d7a5faed336"
        self.bridge = MapBridge()
        self.drawing_mode = False
        self.init_map()

    def init_map(self):
        self.channel = QWebChannel()
        self.channel.registerObject('bridge', self.bridge)
        self.page().setWebChannel(self.channel)
        html_content = self._load_template()
        js_code = self._get_map_js()
        html_with_js = html_content.replace(
            "<!-- JavaScript-код будет подставлен сюда автоматически -->",
            js_code
        )
        self.setHtml(html_with_js, QUrl("about:blank"))
        self.loadFinished.connect(self.on_map_loaded)

    def on_map_loaded(self):
        self.page().runJavaScript("""
            window.currentPlot = null;
            window.drawingMode = false;
            window.clickPoints = [];
            window.polygon = null;
            window.plotObjects = [];
        """)

    def _load_template(self):
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Yandex Map</title>
    <script src="https://api-maps.yandex.ru/2.1/?apikey={self.API_KEY}&lang=ru_RU" type="text/javascript"></script>
    <script src="qrc:///qtwebchannel/qwebchannel.js" type="text/javascript"></script>
    <style>
        html, body {{
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
        }}
        #map {{
            width: 100%;
            height: 100%;
        }}
        .map-status {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: white;
            padding: 5px 10px;
            z-index: 1000;
            border-radius: 3px;
            box-shadow: 0 0 5px rgba(0,0,0,0.3);
        }}
    </style>
</head>
<body>
    <div class="map-status">Инициализация карты.</div>
    <div id="map"></div>
    <script type="text/javascript">
        <!-- JavaScript-код будет подставлен сюда автоматически -->
    </script>
</body>
</html>"""

    def _get_map_js(self):
        return """
        var map;
        var polygon;
        var clickPoints = [];
        var searchControl;

        // После загрузки WebChannel создаём bridge
        new QWebChannel(qt.webChannelTransport, function(channel) {
            window.bridge = channel.objects.bridge;
        });

        ymaps.ready(init);

        function init() {
            document.querySelector('.map-status').textContent = 'Загрузка карты...';

            map = new ymaps.Map('map', {
                center: [52.982869, 37.397889],
                zoom: 13,
                type: 'yandex#hybrid',
                controls: ['zoomControl', 'typeSelector']
            });

            // Поисковая панель
            searchControl = new ymaps.control.SearchControl({
                options: {
                    provider: 'yandex#search',
                    noPlacemark: true,
                    placeholderContent: 'Поиск адреса',
                    size: 'large'
                }
            });
            map.controls.add(searchControl, { float: 'left' });

            searchControl.events.add('resultselect', function(e) {
                var index = e.get('index');
                searchControl.getResult(index).then(function(res) {
                    var coords = res.geometry.getCoordinates();
                    map.panTo(coords, {
                        flying: true,
                        checkZoomRange: true
                    });
                });
            });

            // Обработка клика: рисование полигона
            map.events.add('click', function(e) {
                if (window.drawingMode && window.bridge) {
                    var coords = e.get('coords');
                    clickPoints.push(coords);
                    bridge.add_point(coords[0], coords[1]);

                    if (polygon) {
                        map.geoObjects.remove(polygon);
                    }
                    polygon = new ymaps.Polygon([clickPoints], {}, {
                        strokeColor: '#FF0000',
                        fillColor: '#FF000080',
                        strokeWidth: 2
                    });
                    map.geoObjects.add(polygon);
                }
            });

            document.querySelector('.map-status').textContent = 'Карта готова';
            setTimeout(function() {
                document.querySelector('.map-status').style.display = 'none';
            }, 1000);
        }

        function getStatusColor(status) {
            if (!status) return {stroke: '#000000', fill: '#00000040', text: '#FFFFFF'};
            status = status.toLowerCase();

            // Опционально, для любых статусов, начинающихся на «засеяно»
            if (status.startsWith('засеяно')) {
                return {stroke: '#228B22', fill: '#228B2240', text: '#FFFFFF'};
            }

            var colors = {
                'новый':                     {stroke: '#FF0000', fill: '#FF000040', text: '#FFFFFF'}, // красный
                'подготовка почвы':          {stroke: '#FFA500', fill: '#FFA50040', text: '#000000'}, // оранжевый
                'посев':                     {stroke: '#3CB371', fill: '#3CB37140', text: '#000000'},
                'уход за посевами':          {stroke: '#1E90FF', fill: '#1E90FF40', text: '#FFFFFF'}, // ярко‑синий
                'защита растений':           {stroke: '#8A2BE2', fill: '#8A2BE240', text: '#FFFFFF'}, // фиолетовый
                'уборка урожая':             {stroke: '#A52A2A', fill: '#A52A2A40', text: '#FFFFFF'}, // кирпично‑коричневый
                'послеуборочная обработка':  {stroke: '#CD5C5C', fill: '#CD5C5C40', text: '#FFFFFF'}, // индийская красная
                'отдых':                     {stroke: '#808080', fill: '#80808040', text: '#000000'}, // средне‑серый
                'default':                   {stroke: '#000000', fill: '#00000040', text: '#FFFFFF'}
            };

            return colors[status] || colors['default'];
        }


        // Рисует один участок (используется при выделении)
        function drawPlot(coordinates, name, status, crop, isHighlighted) {
            if (window.currentPlot) {
                map.geoObjects.remove(window.currentPlot);
                window.currentPlot = null;
            }

            var color = getStatusColor(status);

            var poly = new ymaps.Polygon([coordinates], {
                hintContent: name,
                balloonContent:
                    '<b>' + name + '</b>' +
                    '<br>Статус: ' + status +
                    (crop ? '<br>Культура: ' + crop : '')
            }, {
                // ВСЕГДА используем palette.stroke / palette.fill
                strokeColor: color.stroke,
                fillColor:   color.fill,
                // для визуального выделения можно увеличить ширину контура
                strokeWidth: isHighlighted ? 3 : 2,
                opacity: 0.7
            });

            var center = ymaps.util.bounds.getCenter(
                ymaps.util.bounds.fromPoints(coordinates)
            );

            var labelContent = '<div style="' +
                'background:' + color.fill + ';' +
                'color:' + color.text + ';' +
                'padding:5px;border-radius:3px;font-weight:bold;text-align:center;' +
                '">' +
                name +
                '<br><small>Статус: ' + status + (crop ? '<br>Культура: ' + crop : '') + '</small>' +
                '</div>';

            var label = new ymaps.Placemark(center, {
                iconContent: labelContent
            }, {
                preset: 'islands#transparentDotIcon',
                iconLayout: 'default#imageWithContent',
                iconImageHref: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>',
                iconImageSize: [1, 1],
                iconContentOffset: [0, 0],
                hideIconOnBalloonOpen: false
            });

            var coll = new ymaps.GeoObjectCollection();
            coll.add(poly);
            coll.add(label);

            window.currentPlot = coll;
            map.geoObjects.add(coll);

            if (isHighlighted) {
                map.setBounds(coll.getBounds(), { checkZoomRange: true });
            }
        }

        // Очищает все полигоны, которые ранее нарисовали через drawAllPlots
        function clearAllPlots() {
            if (window.plotObjects && window.plotObjects.length > 0) {
                window.plotObjects.forEach(function(obj) {
                    map.geoObjects.remove(obj);
                });
            }
            window.plotObjects = [];
            // Также удаляем единичный poly, если есть
            if (window.currentPlot) {
                map.geoObjects.remove(window.currentPlot);
                window.currentPlot = null;
            }
        }

        // Рисует все участки без использования ObjectManager
        function drawAllPlots(plotsData) {
            clearAllPlots();

            window.plotObjects = [];
            var allPoints = [];

            plotsData.forEach(function(plot) {
                var coords = plot.coordinates;
                if (coords && coords.length > 0) {
                    var color = getStatusColor(plot.status);

                    // Создаём полигон
                    var poly = new ymaps.Polygon([coords], {
                        hintContent: plot.name,
                        balloonContent: '<b>' + plot.name + '</b><br>Статус: ' + plot.status +
                                        (plot.crop ? '<br>Культура: ' + plot.crop : '')
                    }, {
                        strokeColor: color.stroke,
                        fillColor: color.fill,
                        strokeWidth: 1,
                        opacity: 0.7
                    });

                    // --- ДОБАВЛЯЕМ подпись-метку ---
                    var center = ymaps.util.bounds.getCenter(
                        ymaps.util.bounds.fromPoints(coords)
                    );

                    var labelContent = '<div style="background:' + color.fill +
                        ';color:' + color.text + ';padding:5px;border-radius:3px;font-weight:bold;text-align:center;">' +
                        plot.name + '<br><small>Статус: ' + plot.status +
                        (plot.crop ? '<br>Культура: ' + plot.crop : '') + '</small></div>';

                    var label = new ymaps.Placemark(center, {
                        iconContent: labelContent
                    }, {
                        preset: 'islands#transparentDotIcon',
                        iconLayout: 'default#imageWithContent',
                        iconImageHref: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>',
                        iconImageSize: [1, 1],
                        iconContentOffset: [0, 0],
                        hideIconOnBalloonOpen: false
                    });

                    var coll = new ymaps.GeoObjectCollection();
                    coll.add(poly);
                    coll.add(label);

                    map.geoObjects.add(coll);
                    window.plotObjects.push(coll);

                    coords.forEach(function(pt) {
                        allPoints.push(pt);
                    });
                }
            });

            if (allPoints.length > 0) {
                var bounds = ymaps.util.bounds.fromPoints(allPoints);
                map.setBounds(bounds, { checkZoomRange: true });
            }
        }


        // Выделяет и центрирует конкретный участок
        function highlightPlot(coordinates, name, status, crop) {
            drawPlot(coordinates, name, status, crop, true);
        }
        """

    def draw_plot(self, coordinates, name="", status="", crop="", zoom_to=False):
        """
        Отрисовывает один участок с подписью и, при zoom_to=True, центрирует карту.
        """
        coords_json = json.dumps(coordinates, ensure_ascii=False)
        js = f"drawPlot({coords_json}, '{name}', '{status}', '{crop}', {str(zoom_to).lower()});"
        self.page().runJavaScript(js)

    def draw_all_plots(self, plots_data):
        filtered_plots = []
        if not plots_data:
            print("draw_all_plots -> Нет данных для отрисовки.")
            self.page().runJavaScript("drawAllPlots([]);")
            return
        for plot in plots_data:
            coords = plot.get('coordinates')
            if coords:
                filtered_plots.append({
                    'coordinates': coords,
                    'name': plot.get('name', ''),
                    'status': plot.get('status', ''),
                    'crop': plot.get('crop', ''),
                })
        print("draw_all_plots -> данные:", json.dumps(filtered_plots, ensure_ascii=False))
        data_js = json.dumps(filtered_plots, ensure_ascii=False)
        self.page().runJavaScript(f"drawAllPlots({data_js});")

    def highlight_plot(self, coordinates, name, status, crop):
        coords_json = json.dumps(coordinates, ensure_ascii=False)
        js = f"highlightPlot({coords_json}, '{name}', '{status}', '{crop}');"
        self.page().runJavaScript(js)

    def clear_plot(self):
        self.page().runJavaScript("if(window.currentPlot) { map.geoObjects.remove(window.currentPlot); window.currentPlot = null; }")

    def clear_all_plots(self):
        self.page().runJavaScript("clearAllPlots();")

    def toggle_drawing_mode(self, enable: bool = None):
        if enable is None:
            self.drawing_mode = not self.drawing_mode
        else:
            self.drawing_mode = bool(enable)
        self.bridge.current_coordinates = []
        self.page().runJavaScript(f"""
            window.clickPoints = [];
            if (window.polygon) {{
                map.geoObjects.remove(window.polygon);
                window.polygon = null;
            }}
            window.drawingMode = {str(self.drawing_mode).lower()};
        """)
