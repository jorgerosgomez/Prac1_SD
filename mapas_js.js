// Objeto para manejar el estado y funcionalidades del mapa de drones
var DroneMapApp = (function() {
    // Elementos del DOM que usaremos
    var Mapa = document.querySelector('.Mapa-drones');
    var botonocultar = document.getElementById('ocultarMapa');
    var mapSize = 20; // Tamaño del mapa
    

    function fetchDronePositions() {
        fetch('http://127.0.0.1:5000/drones')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(drones => {
                // Limpiar el mapa antes de actualizar las posiciones
                clearDronePositions();
                
                // Recorre cada dron y actualiza su posición
                drones.forEach(drone => {
                    console.log(drone)
                    updateDronePosition(drone.identificador, drone.posicion[0], drone.posicion[1]);
                });
            })
            .catch(error => {
                console.error('There was an error fetching the drone positions:', error);
            });
    }
    function clearDronePositions() {
        const allCells = document.querySelectorAll('.drone-map-cell');
        allCells.forEach(cell => {
            cell.textContent = ''; // Eliminar el identificador del dron
            cell.classList.remove('drone-present'); // Eliminar la clase que indica la presencia de un dron
        });
    }

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
        // Primero, elimina la clase 'drone-present' de todas las celdas para limpiar estados anteriores
        document.querySelectorAll('.drone-map-cell.drone-present').forEach(cell => {
            cell.classList.remove('drone-present');
        });
    
        // Encuentra la celda correspondiente a las coordenadas (x, y)
        const cellSelector = `.drone-map-cell[data-row="${y}"][data-col="${x}"]`;
        const cell = document.querySelector(cellSelector);
        
        // Asegúrate de que la celda existe para evitar errores
        if(cell) {
            // Actualiza el contenido de la celda con el ID del dron y cambia el color de fondo a verde
            cell.textContent = droneId;
            cell.classList.add('drone-present');
        }
    }

    // Inicializa el mapa y los botones
    function init() {
        // Ocultar el mapa inicialmente
        Mapa.style.display = 'grid';
        // Añadir el evento de clic al botón
        botonocultar.addEventListener('click', MapaEsVisible);
        // Crear el mapa de drones
        CrearMapa();
        setInterval(fetchDronePositions,1000);
    
    }

    // Revelar las funciones públicas
    return {
        init: init,
        updateDronePosition: updateDronePosition
    };
})();

// Cuando el contenido del DOM se haya cargado, inicializa la aplicación de mapa de drones
document.addEventListener('DOMContentLoaded', DroneMapApp.init);
