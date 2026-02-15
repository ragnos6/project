const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    baseUrl: "http://127.0.0.1:8001",
  },
  env: {
    MANAGER_USER: "hunter_test",
    MANAGER_PASS: "Zhjl1905",
    ENTERPRISE_ID: 1,
  },
});
