// Start server
const PORT = config.port;
app.listen(PORT, () => {
  console.log(`🚀 Waterfront Directory server running on port ${PORT}`);
  console.log(`📂 Access at: http://localhost:${PORT}`);
  console.log(`🔐 Authentication required for directory access`);
}); 