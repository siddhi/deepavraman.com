/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: 'class',
    content: ["./output/**/*.{html,js}"],
    theme: {
        extend: {},
    },
    plugins: [
        require('@tailwindcss/typography'),
    ]
}
