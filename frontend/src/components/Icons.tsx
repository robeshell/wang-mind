import React from "react";

export const LogoIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    className={className}
    viewBox="0 0 48 48"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <rect width="48" height="48" rx="8" fill="#FEF2F2" />
    <path
      d="M14 18C14 14.6863 16.6863 12 20 12H28C31.3137 12 34 14.6863 34 18V30C34 33.3137 31.3137 36 28 36H20C16.6863 36 14 33.3137 14 30V18Z"
      fill="#DC2626"
    />
    <path
      fillRule="evenodd"
      clipRule="evenodd"
      d="M24 16C22.8954 16 22 16.8954 22 18C22 19.1046 22.8954 20 24 20C25.1046 20 26 19.1046 26 18C26 16.8954 25.1046 16 24 16ZM20 18C20 15.7909 21.7909 14 24 14C26.2091 14 28 15.7909 28 18C28 20.2091 26.2091 22 24 22C21.7909 22 20 20.2091 20 18Z"
      fill="white"
    />
    <path
      d="M20 26C20 24.8954 20.8954 24 22 24H26C27.1046 24 28 24.8954 28 26V32C28 33.1046 27.1046 34 26 34H22C20.8954 34 20 33.1046 20 32V26Z"
      fill="white"
    />
  </svg>
);

export const EyeIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    className={className}
    viewBox="0 0 48 48"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <rect width="48" height="48" rx="8" fill="#EEF2FF" />
    <path
      fillRule="evenodd"
      clipRule="evenodd"
      d="M24 16C18.4772 16 14 20.4772 14 26C14 31.5228 18.4772 36 24 36C29.5228 36 34 31.5228 34 26C34 20.4772 29.5228 16 24 16ZM22 26C22 24.8954 22.8954 24 24 24C25.1046 24 26 24.8954 26 26C26 27.1046 25.1046 28 24 28C22.8954 28 22 27.1046 22 26Z"
      fill="#4F46E5"
    />
  </svg>
);
