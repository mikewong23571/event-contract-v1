module.exports = {
  // Global Prettier configuration for all supported files
  
  // Basic formatting
  semi: true,
  trailingComma: 'es5',
  singleQuote: true,
  printWidth: 80,
  tabWidth: 2,
  useTabs: false,
  
  // Language-specific settings
  overrides: [
    {
      // JavaScript/TypeScript files
      files: ['*.js', '*.jsx', '*.ts', '*.tsx'],
      options: {
        semi: true,
        singleQuote: true,
        trailingComma: 'es5',
        bracketSpacing: true,
        bracketSameLine: false,
      },
    },
    {
      // JSON files
      files: ['*.json', '*.jsonc'],
      options: {
        printWidth: 120,
        tabWidth: 2,
      },
    },
    {
      // Markdown files
      files: ['*.md', '*.mdx'],
      options: {
        printWidth: 100,
        proseWrap: 'always',
        tabWidth: 2,
      },
    },
    {
      // YAML files
      files: ['*.yml', '*.yaml'],
      options: {
        printWidth: 120,
        tabWidth: 2,
        singleQuote: true,
      },
    },
    {
      // HTML files
      files: ['*.html'],
      options: {
        printWidth: 120,
        tabWidth: 2,
        bracketSameLine: true,
      },
    },
    {
      // CSS/SCSS files
      files: ['*.css', '*.scss', '*.less'],
      options: {
        printWidth: 120,
        tabWidth: 2,
        singleQuote: true,
      },
    },
  ],
  
  // Plugins for additional file type support
  plugins: [
    'prettier-plugin-tailwindcss', // For TailwindCSS class sorting
  ],
  
  // TailwindCSS plugin configuration
  tailwindConfig: './frontend/tailwind.config.js',
  tailwindAttributes: ['class', 'className', 'ngClass'],
  
  // File patterns to ignore
  ignorePath: '.prettierignore',
};