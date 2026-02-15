describe('Cars: E2E smoke', () => {
  it('Login -> enterprises -> vehicles -> vehicle info', () => {
    // 1) Открыть страницу логина
    cy.visit('/cars/login/')

    // 2) Ввести логин/пароль и отправить форму
    // Лучше использовать data-cy, но можно и #id, как в статье
    cy.get('[name="username"]').type('hunter')
    cy.get('[name="password"]').type('Zhjl1905')
    cy.get('form').submit()

    // 3) Проверить, что логин успешен (пример: попали на список предприятий)
    cy.visit('/cars/enterprises_list/')
    cy.contains('Предприятия')  // замените на текст, который реально есть на странице

    // 4) Открыть транспорт предприятия (пример для enterprise_id=1)
    cy.visit('/cars/enterprises/1/vehicles/')
    cy.contains('Транспорт')    // замените на реальный текст/заголовок

    // 5) Открыть карточку авто (пример vehicle_id=10)
    cy.visit('/cars/vehicles/10/info/')
    cy.get('body').should('contain.text', 'Информация') // замените на реальный якорный текст
  })
})
