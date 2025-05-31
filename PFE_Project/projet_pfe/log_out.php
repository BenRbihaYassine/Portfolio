<?php
     $servername = "localhost";
     $username = "root";
     $password = "";
     $dbname = "User";
    try{
        $dbco = new PDO("mysql:host=$servername;dbname=$dbname", $username, $password);
        $dbco->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION); 
    }
    catch(PDOException $e){
        echo "Erreur : " . $e->getMessage();
    }
session_start();
session_destroy();
header('Location: index.php');
exit();

?>
