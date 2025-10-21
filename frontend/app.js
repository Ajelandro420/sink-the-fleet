const API_URL = "http://localhost:8000";
let jugador = "Anònim";

// DOM
const bloc1 = document.getElementById('bloc1');
const bloc2 = document.getElementById('bloc2');
const bloc3 = document.getElementById('bloc3');
const tableroDiv = document.getElementById('tablero');
const mensajeVictoria = document.getElementById('mensajeVictoria');

document.getElementById('btnComencar').addEventListener('click', async () => {
    const filas = parseInt(document.getElementById('files').value);
    const columnas = parseInt(document.getElementById('columnes').value);
    jugador = document.getElementById('jugador').value || "Anònim";

    try {
        await fetch(`${API_URL}/crearPartida`, {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({filas,columnas,jugador})
        });
        mostrarBlocs(filas,columnas);
    } catch(e){console.error(e);}
});

function mostrarBlocs(filas,columnas){
    bloc1.style.display="none";
    bloc2.style.display="flex";
    bloc3.style.display="flex";
    generarTablero(filas,columnas);
}

function generarTablero(filas,columnas){
    tableroDiv.style.gridTemplateColumns = `repeat(${columnas},40px)`;
    tableroDiv.style.gridTemplateRows = `repeat(${filas},40px)`;
    tableroDiv.innerHTML = '';
    for(let i=0;i<filas;i++){
        for(let j=0;j<columnas;j++){
            const c=document.createElement('div');
            c.className='casilla';
            c.dataset.fila=i;
            c.dataset.columna=j;
            c.addEventListener('click',()=>dispararCasilla(i,j,c));
            tableroDiv.appendChild(c);
        }
    }
}

async function dispararCasilla(fila,columna,casilla){
    if(casilla.classList.contains('disparada')) return;

    try{
        const r=await fetch(`${API_URL}/disparar?fila=${fila}&columna=${columna}`,{method:'POST'});
        const data=await r.json();

        casilla.classList.add('disparada');
        casilla.style.cursor='not-allowed';

        if(data.resultado==='tocado') {casilla.classList.add('tocado'); casilla.textContent='💥';}
        else if(data.resultado==='hundido') {casilla.classList.add('hundido'); casilla.textContent='☠️';}
        else {casilla.classList.add('agua'); casilla.textContent='💧';}

        // Stats
        document.getElementById('dispars').textContent=data.dispars;
        document.getElementById('encerts').textContent=data.encerts;
        document.getElementById('enfonsats').textContent=data.vaixells_hundidos;
        document.getElementById('puntuacio').textContent=data.puntuacio;

        // Ganar
        if(data.vaixells_hundidos>=5){
            mensajeVictoria.textContent=`¡Felicidades, ${jugador}! Has hundido todos los barcos.`;
            mensajeVictoria.style.display='block';
            setTimeout(()=>mensajeVictoria.style.display='none',3000);

            document.querySelectorAll('.casilla').forEach(c=>c.classList.add('disparada'));
        }

    } catch(e){console.error(e);}
    
}
