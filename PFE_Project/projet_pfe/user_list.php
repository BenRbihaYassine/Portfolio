<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>User Management</title>
    <link rel="stylesheet" href="sty.css">
</head>
<body>
<div class="sidebar">
<img src="logo_blue_m.png" alt="">
    <ul>
      <li><a href="dashboard.html">Dashboard</a></li>
      <li><a href="sinistre.html">Sinistre</a></li>
      <li><a href="production.html">Production</a></li>
      <li><a href="add_user.php">Add User</a></li>
      <li><a class="active" href="#">User List</a></li>
      <li><a href="log_out.php">Déconnexion</a></li>
    </ul>
  </div>
  <div class="content">
    <h1>User Management</h1>
    <table>
        <thead>
            <tr>
                <th>Matricule</th>
                <th>Username</th>
                <th>Department</th>
                <th>Action</th>
            </tr>
        </thead>
        <tbody>
            <?php include 'fetch_users.php'; ?>
        </tbody>
    </table>
    </div>
</body>
</html>

