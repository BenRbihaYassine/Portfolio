<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Assurance</title>
    <style>
        html, body {
            margin: 0;
            padding: 0;
            width: 100%;
            height: 500px;
        }
        .dashboard-container {
            width: 100%;
            height: 500px;
        }
        .dashboard-container iframe {
            width: 100%;
            height: 500px;
        }
    </style>
</head>
<body>
    <header>
        <h1>Dashboard Assurance</h1>
    </header>
    <main>
        <div class="dashboard-container">
        <iframe title="production" width="600" height="373.5" src="https://app.powerbi.com/view?r=eyJrIjoiZTAxODdjZTEtZjYyNi00YzdkLTkzNzAtZTkzMzFlY2ZhYWE5IiwidCI6ImRiZDY2NjRkLTRlYjktNDZlYi05OWQ4LTVjNDNiYTE1M2M2MSIsImMiOjl9" frameborder="0" allowFullScreen="true"></iframe>
        </div>
    </main>
    <button type="submit" form="logout-form">Déconnexion</button>
        <form id="logout-form" method="post" action="log_out.php">
            <input type="hidden" name="logout" value="true">
        </form>
</body>
</html>
