<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login Page</title>
    <link rel="stylesheet" href="s1.css">
</head>
<body>
    <div class="container">
        <img src="logo_blue.png" alt="">
        <form method="post">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" placeholder="Enter your username">
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" placeholder="Enter your password">
            </div>
            <button type="submit" name="submit">Login</button>
        </form>
    </div>
    <?php
$servername = "localhost";
$username = "root";
$password = "";
$dbname = "user";

try {
    $dbco = new PDO("mysql:host=$servername;dbname=$dbname", $username, $password);
    $dbco->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    if(isset($_POST['submit'])){
        $username = $_POST['username'];
        $pass = $_POST['password'];

        // Fetch hashed password and department of the user from the database
        $stmt0 = $dbco->prepare("SELECT Pass_word, Department_id FROM `user_tab` WHERE Username = :Username");
        $stmt0->execute(array(':Username' => $username));
        $result = $stmt0->fetch(PDO::FETCH_ASSOC);

        if($result) {
            $hashed_password = $result['Pass_word'];
            $department_id = $result['Department_id'];

            // Verify the password
            if(password_verify($pass, $hashed_password)){
                // Start a new session
                session_start();

                // Store the username and department_id in the session
                $_SESSION['username'] = $username;
                $_SESSION['department_id'] = $department_id;

                // Determine the redirect URL based on the department
                switch($department_id) {
                    case 1:
                        header('Location: cm_dashboard.html');
                        break;
                    case 2:
                        header('Location: cp_dashboard.html');
                        break;
                    case 3:
                        header('Location: D_dashboard.html');
                        break;
                    case 4:
                        header('Location: D_dashboard.html');
                        break;
                    default:
                        header('Location: dashboard.html'); // Redirect to a generic dashboard if department_id is not recognized
                }
                exit();
            } else {
                // Incorrect password
                $message = 'Incorrect username or password!';
                echo "<script>alert('$message');</script>";
            }
        } else {
            // Username not found
            $message = 'User not found!';
            echo "<script>alert('$message');</script>";
        }
    }
} catch(PDOException $e) {
    echo "Error: " . $e->getMessage();
}
?>


</body>
</html>
