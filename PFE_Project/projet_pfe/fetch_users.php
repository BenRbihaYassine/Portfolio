<?php
// Connexion à la base de données
$servername = "localhost";
$username = "root";
$password = "";
$dbname = "user";

try {
    $dbco = new PDO("mysql:host=$servername;dbname=$dbname", $username, $password);
    $dbco->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    // Récupération des utilisateurs
    $stmt = $dbco->query("SELECT Matricule, Username, D.Department FROM user_tab U ,Department D WHERE D.Department_id=U.Department_id and D.Department != 'Admin'");
    while ($row = $stmt->fetch()) {
        echo "<tr>";
        echo "<td>" . $row['Matricule'] . "</td>";
        echo "<td>" . $row['Username'] . "</td>";
        echo "<td>" . $row['Department'] . "</td>";
        echo "<td>
        <form method='post'>
            <input type='hidden' name='matricule' value='" . $row['Matricule'] . "'>
            <button type='submit' name='delete_user' class='delete-button'>Supprimer</button>
        </form>
    </td>";
        echo "</tr>";
    }
    if(isset($_POST['delete_user'])){
        // Récupérer le matricule de l'utilisateur à supprimer
        $matricule = $_POST['matricule'];
    
        try {
            // Préparation de la requête de suppression
            $stmt = $dbco->prepare("DELETE FROM user_tab WHERE Matricule = :matricule");
            $stmt->bindParam(':matricule', $matricule);
            
            // Exécution de la requête
            if ($stmt->execute()) {
                // Redirection vers la même page après la suppression
                header("Location: user_list.php");
                exit();
            } else {
                echo "Erreur lors de la suppression de l'utilisateur.";
            }
        } catch(PDOException $e) {
            echo "Erreur : " . $e->getMessage();
        }
    }
    
} catch(PDOException $e) {
    echo "Erreur : " . $e->getMessage();
}
?>