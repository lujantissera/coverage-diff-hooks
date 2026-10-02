# PHP rules (PHPUnit)

Applies when the blocking hook is `coverage-diff-php`.

## Where tests go

Follow the project settings. Without them, mirror the existing tests folder. Test
classes are named `<ClassName>Test`, extend `PHPUnit\Framework\TestCase`, and test
methods are named `test<Behavior>`.

## Style

- Use assertions on the result: `assertSame`, `assertEquals`, `assertTrue`,
  `assertCount`, `expectException`.
- Use `@dataProvider` (or the `#[DataProvider]` attribute) for several inputs of the
  same behavior.
- Build only the objects and properties the code actually reads. PHP warns when
  reading an unset property, and a project may turn warnings into test failures.
- Use `setUp()` for shared preparation.

## External dependencies

- Replace database, file, HTTP and global state with test doubles
  (`createMock`, `createStub`) or the project's stubs. Never mock the class under test.
- Include or require the real production class, so the test runs against real code.

## Running

The hook runs PHPUnit with `--coverage-clover`. To check one test quickly:

```bash
vendor/bin/phpunit --filter <TestName>
```

The folder of the file under test must be included in the `<coverage>` section of
`phpunit.xml`, or it will not appear in the report.
