##map_widget.py
from map.map_loader import MapLoader
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QObject, pyqtSlot, QUrl
from PyQt5.QtWebChannel import QWebChannel
import os

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
        
        # Для отладки карты (если нужно)
        # os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = '9222'

    def init_map(self):
        self.channel = QWebChannel()
        self.channel.registerObject('bridge', self.bridge)
        self.page().setWebChannel(self.channel)

        html_content = self._load_template()
        js_code = self._get_map_js()
        html_content = html_content.replace("</script>", f"{js_code}</script>")
        
        self.setHtml(html_content, QUrl("about:blank"))
        self.loadFinished.connect(self.on_map_loaded)

    def on_map_loaded(self):
        """Вызывается после загрузки карты"""
        self.page().runJavaScript("""
            window.plots = [];
            window.currentPlot = null;
        """)

    def _load_template(self):
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Yandex Map</title>
    <script src="https://api-maps.yandex.ru/2.1/?apikey={self.API_KEY}&lang=ru_RU"></script>
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <style>
        #map {{
            width: 100%;
            height: 100vh;
            margin: 0;
            padding: 0;
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
        .plot-label {{
            font-size: 12px;
            font-weight: bold;
            text-align: center;
            padding: 2px 5px;
            background: rgba(255, 255, 255, 0.8);
            border-radius: 3px;
            box-shadow: 0 0 3px rgba(0,0,0,0.3);
        }}
    </style>
</head>
<body>
    <div class="map-status">Инициализация карты...</div>
    <div id="map"></div>
    <script>
        // JavaScript code will be injected here
    </script>
</body>
</html>"""

    def _get_map_js(self):
        return """
        var map;
        var polygon;
        var clickPoints = [];
        var searchControl;
        var objectManager;
        
        new QWebChannel(qt.webChannelTransport, function(channel) {
            window.bridge = channel.objects.bridge;
        });
        
        ymaps.ready(init);
        
        function init() {
            document.querySelector('.map-status').textContent = 'Загрузка карты...';
            
            map = new ymaps.Map('map', {
                center: [52.982869, 37.397889],
                zoom: 13,
                controls: ['zoomControl', 'typeSelector']
            });

            // Инициализация ObjectManager для эффективного управления множеством объектов
            objectManager = new ymaps.ObjectManager({
                clusterize: true,
                gridSize: 64,
                clusterDisableClickZoom: true
            });
            
            map.geoObjects.add(objectManager);
            
            searchControl = new ymaps.control.SearchControl({
                options: {
                    provider: 'yandex#search',
                    noPlacemark: true,
                    placeholderContent: 'Поиск адреса...',
                    size: 'large'
                }
            });
            
            map.controls.add(searchControl, { float: 'left' });

            searchControl.events.add('resultselect', function(e) {
                var index = e.get('index');
                searchControl.getResult(index).then(function(res) {
                    var coordinates = res.geometry.getCoordinates();
                    map.panTo(coordinates, {
                        flying: true,
                        checkZoomRange: true
                    });
                });
            });

            map.events.add('click', function(e) {
                if(window.drawingMode && window.bridge) {
                    var coords = e.get('coords');
                    clickPoints.push(coords);
                    bridge.add_point(coords[0], coords[1]);
                    
                    if(polygon) map.geoObjects.remove(polygon);
                    polygon = new ymaps.Polygon([clickPoints], {}, {
                        strokeColor: '#FF0000',
                        fillColor: '#FF000080'
                    });
                    map.geoObjects.add(polygon);
                }
            });
            
            document.querySelector('.map-status').textContent = 'Карта готова';
            setTimeout(() => {
                document.querySelector('.map-status').style.display = 'none';
            }, 1000);
        }
        
        function drawPlot(coordinates, name, status, isHighlighted = false) {
            // Удаляем предыдущий выделенный участок, если есть
            if (window.currentPlot) {
                map.geoObjects.remove(window.currentPlot);
            }
            
            // Определяем цвет в зависимости от статуса
            var color = getStatusColor(status);
            
            window.currentPlot = new ymaps.Polygon([coordinates], {
                balloonContent: `<b>${name}</b><br>Статус: ${status}`
            }, {
                strokeColor: isHighlighted ? '#FF0000' : color.stroke,
                fillColor: isHighlighted ? '#FF000060' : color.fill,
                strokeWidth: isHighlighted ? 3 : 2
            });
            
            // Добавляем подпись с названием участка
            var center = ymaps.util.bounds.getCenter(
                ymaps.util.bounds.fromPoints(coordinates)
            );
            
            window.currentPlot.properties.set({
                hintContent: name,
                balloonContent: `<b>${name}</b><br>Статус: ${status}`
            });
            
            map.geoObjects.add(window.currentPlot);
            map.setBounds(window.currentPlot.geometry.getBounds());
        }
        
        function drawAllPlots(plotsData) {
            // Очищаем все предыдущие участки
            objectManager.removeAll();
            
            // Создаем коллекцию объектов для ObjectManager
            var objects = {
                type: 'FeatureCollection',
                features: []
            };
            
            // Рисуем все участки
            plotsData.forEach(function(plot) {
                if (plot.coordinates && plot.coordinates.length > 0) {
                    // Определяем цвет в зависимости от статуса
                    var color = getStatusColor(plot.status);
                    
                    var feature = {
                        type: 'Feature',
                        id: plot.id,
                        geometry: {
                            type: 'Polygon',
                            coordinates: [plot.coordinates]
                        },
                        properties: {
                            hintContent: plot.name,
                            balloonContent: `<b>${plot.name}</b><br>Статус: ${plot.status}`,
                            name: plot.name,
                            status: plot.status
                        },
                        options: {
                            strokeColor: color.stroke,
                            fillColor: color.fill,
                            strokeWidth: 1
                        }
                    };
                    
                    objects.features.push(feature);
                }
            });
            
            // Добавляем все объекты на карту через ObjectManager
            objectManager.add(objects);
            
            // Если есть участки, центрируем карту, чтобы показать все
            if (plotsData.length > 0 && plotsData[0].coordinates) {
                var bounds = ymaps.util.bounds.fromPoints(plotsData[0].coordinates);
                for (var i = 1; i < plotsData.length; i++) {
                    if (plotsData[i].coordinates) {
                        bounds = ymaps.util.bounds.unionBounds(
                            bounds, 
                            ymaps.util.bounds.fromPoints(plotsData[i].coordinates)
                        );
                    }
                }
                map.setBounds(bounds, {checkZoomRange: true});
            }
        }
        
        function highlightPlot(coordinates, name, status) {
            // Находим и выделяем нужный участок
            if (objectManager) {
                objectManager.setFilter(function(object) {
                    var coords = object.geometry.coordinates[0];
                    if (JSON.stringify(coords) === JSON.stringify(coordinates)) {
                        object.options.strokeColor = '#FF0000';
                        object.options.fillColor = '#FF000060';
                        object.options.strokeWidth = 3;
                    } else {
                        var color = getStatusColor(object.properties.status);
                        object.options.strokeColor = color.stroke;
                        object.options.fillColor = color.fill;
                        object.options.strokeWidth = 1;
                    }
                    return true;
                });
                
                // Центрируем на выделенном участке
                var bounds = ymaps.util.bounds.fromPoints(coordinates);
                map.setBounds(bounds, {checkZoomRange: true});
            }
        }
        
        function clearPlot() {
            if (window.currentPlot) {
                map.geoObjects.remove(window.currentPlot);
                window.currentPlot = null;
            }
        }
        
        function clearAllPlots() {
            objectManager.removeAll();
            clearPlot();
        }
        
        function getStatusColor(status) {
            var colors = {
                'Новый': {stroke: '#888888', fill: '#88888840', text: '#000000'},
                'Подготовка почвы': {stroke: '#FFA500', fill: '#FFA50040', text: '#000000'},
                'Посев': {stroke: '#008000', fill: '#00800040', text: '#FFFFFF'},
                'Уход за посевами': {stroke: '#0000FF', fill: '#0000FF40', text: '#FFFFFF'},
                'Защита растений': {stroke: '#800080', fill: '#80008040', text: '#FFFFFF'},
                'Уборка урожая': {stroke: '#006400', fill: '#00640040', text: '#FFFFFF'},
                'Послеуборочная обработка': {stroke: '#A52A2A', fill: '#A52A2A40', text: '#FFFFFF'},
                'Отдых': {stroke: '#D3D3D3', fill: '#D3D3D340', text: '#000000'},
                'default': {stroke: '#888888', fill: '#88888840', text: '#000000'}
            };
            return colors[status] || colors['default'];
        }
        
        window.drawingMode = false;
        """

    def draw_plot(self, coordinates, name="", status="", zoom_to=False):
        """Отрисовывает один участок на карте с названием и статусом"""
        self.page().runJavaScript(f"""
            var color = getStatusColor('{status}');
        
            // Создаем полигон
            var polygon = new ymaps.Polygon([{coordinates}], {{
                hintContent: '{name}',
                balloonContent: '<b>{name}</b><br>Статус: {status}'
            }}, {{
                strokeColor: color.stroke,
                fillColor: color.fill,
                strokeWidth: 3,
                opacity: 0.7
            }});
        
            // Создаем подпись внутри полигона
            var center = ymaps.util.bounds.getCenter(
                ymaps.util.bounds.fromPoints({coordinates})
            );
        
            var label = new ymaps.Placemark(center, {{
                iconContent: [
                    '<div style="background: ' + color.fill + ';',
                    'color: ' + color.text + ';',
                    'padding: 5px; border-radius: 3px;',
                    'font-weight: bold; text-align: center;">',
                    '{name}<br>',
                    '<small>Статус: {status}</small>',
                    '</div>'
                ].join('')
            }}, {{
                preset: 'islands#transparentDotIcon',
                iconLayout: 'default#imageWithContent',
                iconImageHref: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>',
                iconImageSize: [1, 1],
                iconContentOffset: [0, 0],
                hideIconOnBalloonOpen: false
            }});
        
            // Группируем объекты
            var objectCollection = new ymaps.GeoObjectCollection();
            objectCollection.add(polygon);
            objectCollection.add(label);
        
            // Удаляем старый полигон если есть
            if(window.currentPlot) {{
                map.geoObjects.remove(window.currentPlot);
            }}
        
            window.currentPlot = objectCollection;
            map.geoObjects.add(window.currentPlot);
        
            {f"map.setBounds(window.currentPlot.getBounds());" if zoom_to else ""}
        """)

    def draw_all_plots(self, plots_data):
        """Отрисовывает все участки на карте с названиями и статусами"""
        if not plots_data:
            return
    
        js_code = """
            // Очищаем предыдущие участки
            if (window.plotsCollection) {
                map.geoObjects.remove(window.plotsCollection);
            }
        
            window.plotsCollection = new ymaps.GeoObjectCollection();
            var bounds = null;
        """
    
        for plot in plots_data:
            if plot.get('coordinates'):
                js_code += f"""
                    // Участок {plot.get('id', 0)}
                    var color = getStatusColor('{plot.get('status', 'Новый')}');
                
                    // Полигон
                    var polygon = new ymaps.Polygon([{plot['coordinates']}], {{
                        hintContent: '{plot.get('name', '')}',
                        balloonContent: '<b>{plot.get('name', '')}</b><br>Статус: {plot.get('status', 'Новый')}'
                    }}, {{
                        strokeColor: color.stroke,
                        fillColor: color.fill,
                        strokeWidth: 2,
                        opacity: 0.7
                    }});
                
                    // Подпись
                    var center = ymaps.util.bounds.getCenter(
                        ymaps.util.bounds.fromPoints({plot['coordinates']})
                    );
                
                    var label = new ymaps.Placemark(center, {{
                        iconContent: [
                            '<div style="background: ' + color.fill + ';',
                            'color: ' + color.text + ';',
                            'padding: 5px; border-radius: 3px;',
                            'font-weight: bold; text-align: center;">',
                            '{plot.get('name', '')}<br>',
                            '<small>Статус: {plot.get('status', 'Новый')}</small>',
                            '</div>'
                        ].join('')
                    }}, {{
                        preset: 'islands#transparentDotIcon',
                        iconLayout: 'default#imageWithContent',
                        iconImageHref: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>',
                        iconImageSize: [1, 1],
                        iconContentOffset: [0, 0],
                        hideIconOnBalloonOpen: false
                    }});
                
                    // Группировка
                    var plotGroup = new ymaps.GeoObjectCollection();
                    plotGroup.add(polygon);
                    plotGroup.add(label);
                    window.plotsCollection.add(plotGroup);
                
                    // Обновляем границы
                    var plotBounds = ymaps.util.bounds.fromPoints({plot['coordinates']});
                    bounds = bounds ? ymaps.util.bounds.unionBounds(bounds, plotBounds) : plotBounds;
                """
    
        js_code += """
            // Добавляем все участки на карту
            map.geoObjects.add(window.plotsCollection);
        
            // Центрируем карту
            if (bounds) {
                map.setBounds(bounds, {checkZoomRange: true});
            }
        """
    
        self.page().runJavaScript(js_code)

    def highlight_plot(self, coordinates, name="", status=""):
        """Выделяет указанный участок на карте (при показе всех участков)"""
        self.page().runJavaScript(f"highlightPlot({coordinates}, '{name}', '{status}');")

    def clear_plot(self):
        """Очищает текущий выделенный участок"""
        self.page().runJavaScript("clearPlot();")

    def clear_all_plots(self):
        """Очищает все участки с карты"""
        self.page().runJavaScript("clearAllPlots();")

    def toggle_drawing_mode(self, enabled):
        """Включает/выключает режим рисования"""
        self.drawing_mode = enabled
        self.page().runJavaScript(f"window.drawingMode = {str(enabled).lower()};")
        
        if not enabled:
            self.bridge.current_coordinates = []
            self.page().runJavaScript("""
                if(polygon) {
                    map.geoObjects.remove(polygon);
                    polygon = null;
                }
                clickPoints = [];
            """)

    def draw_existing_plot(self, coordinates, name="", status=""):
        """Отрисовывает существующий участок (для обратной совместимости)"""
        self.draw_plot(coordinates, name, status, zoom_to=True)