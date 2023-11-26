// Objeto para manejar el estado y funcionalidades del mapa de drones
var DroneMapApp = (function() {
    // Elementos del DOM que usaremos
    var Mapa = document.querySelector('.Mapa-drones');
    var botonocultar = document.getElementById('ocultarMapa');
    var mapSize = 20; // Tamaño del mapa

    // Función para crear el mapa de drones
    function CrearMapa() {
        for (let row = 0; row < mapSize; row++) {
            for (let col = 0; col < mapSize; col++) {
                const cell = document.createElement('div');
                cell.classList.add('drone-map-cell'); // Clase para los estilos
                cell.dataset.row = row; // Guardar la fila en dataset
                cell.dataset.col = col; // Guardar la columna en dataset
                Mapa.appendChild(cell);
            }
        }
    }

    // Función para alternar la visibilidad del mapa y cambiar el texto del botón
    function MapaEsVisible() {
        var isMapVisible = Mapa.style.display !== 'grid';
        Mapa.style.display = isMapVisible ? 'grid' : 'none'; // alternar display
        botonocultar.textContent = isMapVisible ? 'Ocultar Mapa' : 'Mostrar Mapa'; // alternar texto
    }

    // Función para actualizar la posición de un dron en el mapa
    function updateDronePosition(droneId, x, y) {
        const cellSelector = `.drone-map-cell[data-row="${y}"][data-col="${x}"]`;
        const cell = document.querySelector(cellSelector);
        cell.textContent = droneId; // Ejemplo simple: poner el ID del dron en la celda
        cell.classList.add('drone-present'); // Suponiendo que tienes estilos para esta clase
    }

    // Inicializa el mapa y los botones
    function init() {
        // Ocultar el mapa inicialmente
        Mapa.style.display = 'grid';
        // Añadir el evento de clic al botón
        botonocultar.addEventListener('click', MapaEsVisible);
        // Crear el mapa de drones
        CrearMapa();
    }

    // Revelar las funciones públicas
    return {
        init: init,
        updateDronePosition: updateDronePosition
    };
})();

// Cuando el contenido del DOM se haya cargado, inicializa la aplicación de mapa de drones
document.addEventListener('DOMContentLoaded', DroneMapApp.init);
