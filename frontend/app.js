const API_URL = "http://localhost:8000";
let jugador = "Anonimo";
let totalCasillas = 0;
let dificultad = 0;
let partidaActualId = null;

let bloc1, bloc2, bloc3, blocRanking, tableroDiv, mensajeVictoria, sonidos = {};

document.addEventListener('DOMContentLoaded', () => {
    bloc1 = document.getElementById('bloc1');
    bloc2 = document.getElementById('bloc2');
    bloc3 = document.getElementById('bloc3');
    blocRanking = document.getElementById('blocRanking');
    tableroDiv = document.getElementById('tablero');
    mensajeVictoria = document.getElementById('mensajeVictoria');

    sonidos = {
        tocado: document.getElementById('hit'),
        hundido: document.getElementById('sunken'),
        agua: document.getElementById('miss'),
        ganar: document.getElementById('win'),
        perder: document.getElementById('lose')
    };
});

function reproducirSonido(tipo) {
    if (sonidos[tipo]) {
        sonidos[tipo].currentTime = 0;
        sonidos[tipo].play().catch(e => console.log('Error reproduciendo sonido:', e));
    }
}

function registrarMovimiento(texto) {
    const lista = document.getElementById("listaMovimientos");
    const li = document.createElement("li");
    li.textContent = texto;
    lista.prepend(li);
}

async function cargarRanking() {
    try {
        const res = await fetch(`${API_URL}/ranking`);
        const data = await res.json();

        const rankingList = document.getElementById("ranking");
        rankingList.innerHTML = "";

        if (data.length === 0) {
            rankingList.innerHTML = "<li>No hay partidas aún</li>";
            return;
        }

        data.slice(0, 10).forEach((item, i) => {
            const li = document.createElement("li");
            li.textContent = `${i + 1}. ${item.jugador} — ${item.puntuacion} pts`;
            rankingList.appendChild(li);
        });
    } catch (e) {
        console.error("Error cargando ranking:", e);
        document.getElementById("ranking").innerHTML = "<li>Error al cargar ranking</li>";
    }
}

document.getElementById('btnComencar').addEventListener('click', async () => {
    const filas = parseInt(document.getElementById('files').value);
    const columnas = parseInt(document.getElementById('columnes').value);
    totalCasillas = filas * columnas;
    dificultad = document.querySelector('input[name="dificultat"]:checked').value;

    jugador = document.getElementById('jugador').value || "Anònim";

    try {
        const response = await fetch(`${API_URL}/crearPartida`, {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({filas,columnas,jugador})
        });
        const data = await response.json();
        partidaActualId = data.id_partida;

        mostrarBlocs(filas,columnas);
        cargarRanking();
    } catch(e){console.error(e);}
});

document.getElementById('btnAbandonar').addEventListener('click', reiniciarJuego);

function reiniciarJuego() {
    partidaActualId = null;

    bloc2.style.display = "none";
    bloc3.style.display = "none";
    blocRanking.style.display = "none";
    bloc1.style.display = "flex";

    tableroDiv.innerHTML = "";

    document.getElementById('dispars').textContent = "0";
    document.getElementById('encerts').textContent = "0";
    document.getElementById('enfonsats').textContent = "0";
    document.getElementById('puntuacio').textContent = "0";

    mensajeVictoria.style.display = "none";

    try {
        fetch(`${API_URL}/abandonar`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({partida_id: partidaActualId})
        });
    } catch (e) {console.error(e);}
    console.log("Juego reiniciado");
}

function mostrarBlocs(filas,columnas){
    bloc1.style.display="none";
    bloc2.style.display="flex";
    bloc3.style.display="flex";
    blocRanking.style.display="flex";
    generarTablero(filas,columnas);
}

function generarTablero(filas,columnas){
    tableroDiv.style.gridTemplateColumns = `repeat(${columnas},1fr)`;
    tableroDiv.style.gridTemplateRows = `repeat(${filas},1fr)`;
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

function perder() {
    reproducirSonido('perder');
    mensajeVictoria.textContent=`¡Lo siento, ${jugador}! Has alcanzado el límite de disparos.`;
    mensajeVictoria.style.display='block';
    setTimeout(()=>mensajeVictoria.style.display='none',3000);
    document.querySelectorAll('.casilla').forEach(c=>c.classList.add('disparada'));
    cargarRanking();
}

function ganar() {
    reproducirSonido('ganar');
    mensajeVictoria.textContent=`¡Felicidades, ${jugador}! Has hundido todos los barcos.`;
    mensajeVictoria.style.display='block';
    setTimeout(()=>mensajeVictoria.style.display='none',3000);
    document.querySelectorAll('.casilla').forEach(c=>c.classList.add('disparada'));
    cargarRanking();
}

async function dispararCasilla(fila,columna,casilla){
    if(casilla.classList.contains('disparada') || casilla.classList.contains('hundido')) return;

    //Validamos
    if (!partidaActualId) {
        alert('Error: No hay partida activa');
        return;
    }

    try{
        const r=await fetch(`${API_URL}/disparar?fila=${fila}&columna=${columna}&partida_id=${partidaActualId}`,{method:'POST'});
        const data=await r.json();

        casilla.classList.add('disparada');
        casilla.style.cursor='not-allowed';

        if(data.resultado==='repetido'){
            alert('¡Ya has disparado a esta casilla! Elige otra.');
            return;
        }
        else if(data.resultado==='tocado') {
            casilla.classList.add('tocado');
            casilla.textContent='💥';
            reproducirSonido('tocado');
            registrarMovimiento(`💥 Tocado en (${fila+1}, ${columna+1})`);

        }
        else if(data.resultado==='hundido') {
            casilla.classList.add('hundido');
            casilla.textContent='☠️';
            reproducirSonido('hundido');
            registrarMovimiento(`☠️ Hundido en (${fila+1}, ${columna+1})`);
        }
        else {
            casilla.classList.add('agua');
            casilla.textContent='💧';
            reproducirSonido('agua');
            registrarMovimiento(`💧 Agua en (${fila+1}, ${columna+1})`);
        }

        document.getElementById('dispars').textContent=data.dispars;
        document.getElementById('encerts').textContent=data.encerts;
        document.getElementById('enfonsats').textContent=data.vaixells_hundidos;
        document.getElementById('puntuacio').textContent=data.puntuacio;

        if(data.victoria){
            ganar();
            return;
        }

        switch (dificultad) {
            case '1':
                if (Number(data.dispars)>= totalCasillas*0.80){
                    perder();
                }
                break;

            case '2':
                if (Number(data.dispars)>= totalCasillas*0.65){
                    perder();
                }
                break;

            case '3':
                if (Number(data.dispars)>= totalCasillas*0.50){
                    perder();
                }
                break;
        }
    } catch(e){console.error(e);}
}