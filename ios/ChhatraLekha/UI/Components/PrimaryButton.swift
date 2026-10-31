import SwiftUI

/// Accessible branded action button with loading and disabled states.
public struct PrimaryButton: View {
    public let title: String
    public let iconName: String?
    public let isLoading: Bool
    public let isSecondary: Bool
    public let action: () -> Void

    public init(
        title: String,
        iconName: String? = nil,
        isLoading: Bool = false,
        isSecondary: Bool = false,
        action: @escaping () -> Void
    ) {
        self.title = title
        self.iconName = iconName
        self.isLoading = isLoading
        self.isSecondary = isSecondary
        self.action = action
    }

    public var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                if isLoading {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: isSecondary ? .brandPrimary : .white))
                } else if let icon = iconName {
                    Image(systemName: icon)
                        .font(.body.weight(.semibold))
                }
                Text(title)
                    .font(.body.weight(.semibold))
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 14)
            .background(isSecondary ? Color.surfaceBackground : Color.brandPrimary)
            .foregroundColor(isSecondary ? Color.brandPrimary : Color.white)
            .cornerRadius(10)
            .overlay(
                RoundedRectangle(cornerRadius: 10)
                    .stroke(isSecondary ? Color.borderLine : Color.clear, lineWidth: 1)
            )
        }
        .disabled(isLoading)
        .accessibilityLabel(Text(title))
    }
}

