// Objeto para manejar el estado y funcionalidades del mapa de drones
var DroneMapApp = (function() {
    // Elementos del DOM que usaremos
    var Mapa = document.querySelector('.Mapa-drones');
    var botonocultar = document.getElementById('ocultarMapa');
    var mapSize = 20; // Tamaño del mapa
    var botoniniciar = document.getElementById('iniciarEspectaculo')
    var refresh = document.getElementById('refrescar')
    var botonmandarbase = document.getElementById('base')
    var dronePositions = {};


    function refrescar(){ 
        location.reload();
    }
    setInterval(refrescar,5000)

    function mandarbase() {
        // Cambia la URL a la que necesitas enviar la solicitud POST
        fetch('http://192.168.1.17:5000/base', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log(data); 
        })
        .catch(error => {
            console.error('There was an error starting the show:', error);
        });
    }
    function iniciarEspectaculo() {
        // Cambia la URL a la que necesitas enviar la solicitud POST
        fetch('http://192.168.1.17:5000/iniciarEspectaculo', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
               
            },
           
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log(data); // Aquí manejas la respuesta
        })
        .catch(error => {
            console.error('There was an error starting the show:', error);
        });
    }




    

    function fetchDronePositions() {
        fetch('http://192.168.1.17:5000/drones')
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
                console.error('no hy drones', error);
            });
    }
    function clearDronePositions(droneId) {
        // Si el dron ya está en el mapa, limpia su posición actual
        if (dronePositions[droneId]) {
            const { x, y } = dronePositions[droneId];
            const cellSelector = `.drone-map-cell[data-row="${y}"][data-col="${x}"]`;
            const cell = document.querySelector(cellSelector);
            if (cell) {
                cell.textContent = '';
                cell.classList.remove('drone-present');
            }
        }
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
        // Limpia la posición anterior del dron
        clearDronePositions(droneId);
    
        // Encuentra la celda correspondiente a las nuevas coordenadas (x, y)
        const cellSelector = `.drone-map-cell[data-row="${y}"][data-col="${x}"]`;
        const cell = document.querySelector(cellSelector);
    
        // Asegúrate de que la celda existe para evitar errores
        if (cell) {
            // Actualiza el contenido de la celda con el ID del dron y cambia el color de fondo a verde
            cell.textContent = droneId;
            cell.classList.add('drone-present');
            // Actualiza el registro de la posición del dron
            dronePositions[droneId] = { x, y };
        }
    }

    // Inicializa el mapa y los botones
    function init() {
        // Ocultar el mapa inicialmente
        Mapa.style.display = 'grid';
        // Añadir el evento de clic al botón
        botonocultar.addEventListener('click', MapaEsVisible);
        botoniniciar.addEventListener('click', iniciarEspectaculo);
        botonmandarbase.addEventListener("click",mandarbase)
        refresh.addEventListener("click", refrescar)
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
