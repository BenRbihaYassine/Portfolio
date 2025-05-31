<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>INSCRIPTION EMPLOYEE</title>
        <link rel="stylesheet" href="ins.css">
        <script>
        function validateForm() {
        var password = document.getElementById("password").value;
        var confirmPassword = document.getElementById("confirm_password").value;
        if (password.length < 8) {
            alert("Le mot de passe doit comporter au moins 8 caractères.");
            return false;
        }
        if (password != confirmPassword) {
            alert("Les mots de passe ne correspondent pas.");
            return false;
        }
        }
        </script>
    </head>
    <body>
    <div class="sidebar">
    <img src="logo_blue_m.png" alt="">
    <ul>
      <li><a href="dashboard.html">Dashboard</a></li>
      <li><a href="sinistre.html">Sinistre</a></li>
      <li><a href="production.html">Production</a></li>
      <li><a class="active" href="#">Add User</a></li>
      <li><a href="user_list.php">User List</a></li>
      <li><a href="log_out.php">Déconnexion</a></li>
    </ul>
  </div>
        <div class="content">
        <h1>Registration Form</h1>
        <form id='form' method="post" action="add_user.php" onsubmit="return validateForm()">
            <div class="form-group">
                <label for="Matricule">Matricule:</label>
                <input type="text" id="Matricule" name="Matricule">
            </div>
            <div class="form-group">
                <label for="Username">Pseudo:</label>
                <input type="text" id="Username" name="Username" placeholder="choose a Username" required>
            </div>
            <div class="form-group">
                <label for="dept">Depatement:</label>
                <select id="dept" name="dept" required>
                    <option value="1">Commercial</option>
                    <option value="2">Comptabilité</option>
                    <option value="3">Directeur Générale</option>
                    <option value="4">Directeur Contrôle gestion</option>
                </select>
            </div>
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required>
            </div>
            <div class="form-group">
                <label for="confirm_password">Confirm Password:</label>
                <input type="password" id="confirm_password" name="confirm_password" required>
            </div>
            <button type="submit" id="register-button">Register</button>
        </form>
        </div>
        
        <?php
// Connexion à la base de données
            $servername = "localhost"; // Remplacez localhost par l'adresse du serveur MySQL
            $username = "root"; // Remplacez votre_nom_utilisateur par votre nom d'utilisateur MySQL
            $password = ""; // Remplacez votre_mot_de_passe par votre mot de passe MySQL
            $dbname = "user"; // Remplacez votre_nom_bdd par le nom de votre base de données MySQL

// Création de la connexion
            $dbco = new PDO("mysql:host=$servername;dbname=$dbname", $username, $password);
            $dbco->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
            if(isset($_POST["Matricule"]) && isset($_POST["Username"]) && isset($_POST["dept"]) && isset($_POST["password"])) {
            // Récupération des données du formulaire
                $matricule = $_POST['Matricule'];
                $username = $_POST['Username'];
                $password = $_POST['password'];
                $department_id = $_POST['dept'];
                try{
// Hashage du mot de passe
                    $hashed_password = password_hash($password, PASSWORD_DEFAULT);
                    $sth = $dbco->prepare("INSERT INTO user_tab (Matricule, Username, Pass_word, Department_id)  
                  VALUES ('$matricule', '$username', '$hashed_password', '$department_id') ");
                $sth->execute();             }
                catch(PDOException $e){
                    echo "Erreur : " . $e->getMessage();
                }
                header("Location: dashboard.html");
                exit;
        }
        
?>

    </body>
</html>
