describe('Cars: E2E smoke', () => {
  it('Login -> enterprises -> vehicles -> vehicle info', () => {
    // 1) Открыть страницу логина
    cy.visit('/cars/login/')

    // 2) Ввести логин/пароль и отправить форму
    cy.get('[name="username"]').type('hunter')
    cy.get('[name="password"]').type('Zhjl1905')
    cy.get('form').submit()

    // 3) Проверить, что логин успешен 
    cy.visit('/cars/enterprises_list/')
    cy.get('h2').should('have.text', 'Список доступных предприятий')


    // 4) Открыть транспорт предприятия
    cy.visit('/cars/enterprises/3/vehicles/')
    cy.contains('автомобилей')    // замените на реальный текст/заголовок

    // 5) Открыть карточку авто (пример vehicle_id=10)
    cy.visit('/cars/vehicles/10528/info/')
    cy.get('body').should('contain.text', 'Информация') 
  })
})
