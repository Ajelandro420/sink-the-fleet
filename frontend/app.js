console.log("Frontend carregat - Dia 1");

document.getElementById('testBtn').addEventListener('click', async () => {
    try {
        const resposta = await fetch('http://localhost:8000/prova');
        const dades = await resposta.json();
        
        document.getElementById('resultat').innerHTML = 
            `<strong>✅ Backend connectat!</strong><br>
            Estat: ${dades.estat}<br>
            Dia: ${dades.dia}`;
    } catch (error) {
        document.getElementById('resultat').innerHTML = 
            `<strong>❌ Error!</strong><br>
            Assegura't que el backend està actiu`;
    }
});