Cypress.Commands.add('loginManager', () => {

  cy.session([username, password], () => {
    cy.visit('/cars/login/');
    cy.get('[name="hunter"]').clear().type(username);
    cy.get('[name="Zhjl1905]').clear().type(password);
    cy.get('form').submit();
  });
});

