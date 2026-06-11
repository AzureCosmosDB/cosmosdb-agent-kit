const fs = require('fs');
const path = require('path');

describe('sdk-read-item-over-query rule', () => {

  it('should exist', () => {
    const filePath = path.join(
      __dirname,
      '../skills/cosmosdb-best-practices/rules/sdk-read-item-over-query.md'
    );

    const exists = fs.existsSync(filePath);

    expect(exists).toBe(true);
  });

  it('should have frontmatter with title, impact, and tags', () => {
    const filePath = path.join(
      __dirname,
      '../skills/cosmosdb-best-practices/rules/sdk-read-item-over-query.md'
    );

    const content = fs.readFileSync(filePath, 'utf-8');

    expect(content).toMatch(/title:\s*Prefer ReadItem/);
    expect(content).toMatch(/impact:\s*HIGH/);
    expect(content).toMatch(/tags:/);
  });

  it('should contain multi-language examples', () => {
    const filePath = path.join(
      __dirname,
      '../skills/cosmosdb-best-practices/rules/sdk-read-item-over-query.md'
    );

    const content = fs.readFileSync(filePath, 'utf-8');

    expect(content).toMatch(/### \.NET \/ C#/);
    expect(content).toMatch(/### Java/);
    expect(content).toMatch(/### Python/);
    expect(content).toMatch(/### Node\.js/);

    expect(content).toMatch(/ReadItemAsync/);
    expect(content).toMatch(/readItem/);
    expect(content).toMatch(/read_item/);
  });
});
