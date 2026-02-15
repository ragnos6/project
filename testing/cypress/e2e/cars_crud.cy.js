describe('Cars UI CRUD: Vehicle create/edit/delete (color = Серобурый)', () => {
  const enterpriseId = 1;
  const username = 'hunter_test';
  const password = 'Zhjl1905';

  const carColor = 'Серобурый';

  const extractVehicleId = (href) => {
    const m = (href || '').match(/\/cars\/vehicles\/(\d+)\//);
    return m ? m[1] : null;
  };

  before(() => {
    cy.session([username, password], () => {
      cy.visit('/cars/login/');

      cy.get('#id_username:enabled').should('be.visible').clear().type(username);
      cy.get('#id_password:enabled').should('be.visible').clear().type(password);

      cy.get('form').submit();
      cy.contains('Список доступных предприятий'); // якорь успешного логина [web:61]
    });
  });

  it('Create -> Update -> Delete', () => {
    // ---------- CREATE ----------
    cy.visit(`/cars/enterprises/${enterpriseId}/vehicles/`); // [web:35]

    cy.get('button[data-bs-target="#addCarForm"]').click();
    cy.get('#addCarForm').should('have.class', 'show');

    cy.get('#addCarForm').within(() => {
      cy.get('#id_cost').clear().type('123456.78');
      cy.get('#id_year_of_production').clear().type('2022');
      cy.get('#id_mileage').clear().type('111');
      cy.get('#id_color').clear().type(carColor);

      cy.get('#id_transmission').select('automatic');
      cy.get('#id_fuel_type').select('gasoline');
      cy.get('#id_model').select('1');

      cy.contains('button[type="submit"]', 'Добавить').click();
    });

    // На странице должен появиться цвет "Серобурый"
    cy.contains('td', carColor, { timeout: 10000 }).should('exist'); // [web:61]

    // Берём vehicleId из edit-ссылки в ПЕРВОЙ строке с таким цветом (обычно это только что созданная запись)
    cy.contains('td', carColor)
      .parents('tr')
      .first()
      .find('a[href*="/cars/vehicles/"][href$="/edit/"]')
      .invoke('attr', 'href')
      .then((editHref) => {
        const vehicleId = extractVehicleId(editHref);
        expect(vehicleId).to.not.be.null;

        // ---------- UPDATE ----------
        cy.visit(`/cars/vehicles/${vehicleId}/edit/`); // [web:35]
        cy.get('#id_color').clear().type(carColor); // цвет остаётся Серобурый
        cy.get('form').submit();

        // Возвращаемся в список и проверяем: у нашей машины (по ID) цвет Серобурый
        cy.visit(`/cars/enterprises/${enterpriseId}/vehicles/`); // [web:35]
        cy.get(`a[href="/cars/vehicles/${vehicleId}/edit/"]`)
          .parents('tr')
          .should('contain.text', carColor);

        // ---------- DELETE (без click) ----------
        cy.get(`a[href="/cars/vehicles/${vehicleId}/delete/"]`)
          .invoke('attr', 'href')
          .then((deleteHref) => {
            expect(deleteHref, 'deleteHref').to.not.be.null;
            cy.visit(deleteHref); // [web:35]
          });

        cy.get('form').submit();

        // Проверяем, что именно наша запись исчезла (по ID)
        cy.visit(`/cars/enterprises/${enterpriseId}/vehicles/`); // [web:35]
        cy.get(`a[href="/cars/vehicles/${vehicleId}/edit/"]`).should('not.exist');
      });
  });
});

